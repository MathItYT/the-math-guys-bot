from __future__ import annotations

import base64
import os
from pathlib import Path
import pprint
import subprocess
from shutil import rmtree, make_archive
from typing import Literal
import re

import discord
from discord.ext import pages, commands
from pydantic import BaseModel, Field
import requests
import html2text
from googleapiclient.discovery import build
import pymupdf

from the_math_guys_bot import message_history
from the_math_guys_bot.handle_message import handle_message

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name


def highlight_code(code, name, attrs):
    """Highlight a block of code"""
    lexer = get_lexer_by_name(name)
    formatter = HtmlFormatter()

    return highlight(code, lexer, formatter)


client = message_history.client


class PremiumClassifier(BaseModel):
    type: Literal["solve_math", "research", "programming_project", "general_answer"] = Field(
        description=f"El tipo de respuesta que se debe dar al mensaje, dependiendo de lo que este diga. Si se pide resolver un problema matemático, debe ser 'solve_math'. Si te mencionan y es una conversación general, debe ser 'general_answer'. Si se te pide investigar en internet, debe ser 'research'. Si se te pide realizar un programa en Python, debe ser 'programming_project'."
    )
    necessary_answer: Literal["yes", "no"] = Field(description="Si es necesario responder al mensaje, debe ser 'yes'. Si no es necesario responder, debe ser 'no'. Por ejemplo, si el mensaje no dice la palabra 'bot' ni <@BOT_USER_ID>, no te están mencionando ni refiriéndose a ti, y si además de eso, no hay spam, la respuesta no es necesaria y necessary_answer debe ser 'no' obligatoriamente.")


class IsRelated(BaseModel):
    is_related: bool = Field(description="Si el mensaje está relacionado con la búsqueda de información en internet, este campo es verdadero. Si no, es falso.")


class Steps(BaseModel):
    explanation: str
    output: str


class IntelligentMath(BaseModel):
    steps: list[Steps]


class OrderedMessage(BaseModel):
    ordered_message: str | None = Field(description="El mensaje ordenado de forma natural y entendible, paso a paso, sin LaTeX, solo texto plano Unicode. Si Wolfram Alpha no da solución, este campo es nulo.")


class ActionAndPrintableOutput(BaseModel):
    action: str = Field(description="La acción que se debe realizar con la fórmula dada por el usuario. Es un verbo imperativo en inglés.")
    printable_math: str = Field(description="La fórmula dada por el usuario, pero no en formato LaTeX, sino en texto plano usando caracteres unicode.")
    plotting: bool = Field(description="Si se trata solamente de graficar la fórmula, este campo es verdadero. Si no, es falso.")


class WebQuery(BaseModel):
    query: str = Field(description="La consulta que se debe hacer en internet, en texto plano Unicode.")


class FileOrFolder(BaseModel):
    name: str = Field(description="El nombre del archivo o carpeta.")
    description: str = Field(description="La descripción de lo que hace el archivo o lo que contiene la carpeta.")
    is_folder: bool = Field(description="Si es una carpeta, este campo es verdadero. Si es un archivo, es falso.")
    children: list[FileOrFolder] = Field(description="Los archivos o carpetas que contiene esta carpeta. Si es un archivo, este campo es vacío.")



class Proyect(BaseModel):
    project_structure: list[FileOrFolder] = Field(description="La estructura de un proyecto de programación, en el lenguaje que se te especifique o que sea más adecuado, que resuelve el problema planteado en el mensaje.")


class ResearchPaginator(pages.Paginator):
    def __init__(
        self,
        input_message: discord.Message,
        items: list[tuple[str, str]],
        query: str,
        **kwargs
    ):
        items = items[:5]
        super().__init__(
            pages=self.get_pages(input_message, items, query),
            **kwargs
        )
    
    def get_pages(
        self,
        input_message: discord.Message,
        items: list[tuple[str, str]],
        query: str
    ) -> list[discord.Embed]:
        pages: list[discord.Embed] = []
        page_contents: dict[str, str] = {}
        for i, (item, title) in enumerate(items, start=1):
            response = client.beta.chat.completions.parse(
                messages=[{"role": "system", "content": f"Debes determinar si el título de la página indica que el resultado es relevante para la consulta '{query}' o no. Si es relevante, is_related debe ser True. Si no, is_related debe ser False."}, {"role": "user", "content": title}],
                model="gpt-4o-2024-08-06",
                response_format=IsRelated
            )
            is_related = response.choices[0].message.parsed.is_related
            if not is_related:
                continue
            content = requests.get(item).text
            content = html2text.html2text(content)
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": "Debes responder con un resumen del contenido que se te pase. Si hay matemáticas, usa texto plano Unicode, no LaTeX."}, {"role": "user", "content": content}],
                model="gpt-4o-2024-08-06"
            )
            summary = response.choices[0].message.content
            page_contents[item] = summary
            pages.append(discord.Embed(title=f"Resultado {i}", url=item, description=summary))
            pages[-1].set_thumbnail(url=input_message.author.avatar.url)
            pages[-1].set_author(name=input_message.author.display_name, icon_url=input_message.author.avatar.url)
        total_summary = "\n\n".join([f"{i}. {page_contents[item]}\nSource: {item}" for i, item in enumerate(page_contents, start=1)])
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": "Debes responder con un resumen de todos los resultados de la búsqueda en internet. Si hay matemáticas, usa texto plano Unicode, no LaTeX."}, {"role": "user", "content": total_summary}],
            model="gpt-4o-2024-08-06"
        )
        total_summary = response.choices[0].message.content
        pages.append(discord.Embed(title="Resumen", description=total_summary))
        pages[-1].set_thumbnail(url=input_message.author.avatar.url)
        pages[-1].set_author(name=input_message.author.display_name, icon_url=input_message.author.avatar.url)
        return pages


class Code(BaseModel):
    code: str = Field(description="El código Python que resuelve un problema planteado en un mensaje. No debe tener resaltado con Markdown ni ningún texto acompañando, solo código.")


async def get_images(message: discord.Message) -> list[tuple[str, str]]:
    images = []
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith("image/"):
                image_data = await attachment.read()
                image_data = base64.b64encode(image_data).decode()
                images.append((attachment.content_type, image_data))
    return images


def get_project_structure_str(project_structure: list[FileOrFolder], level: int = 0) -> str:
    project_structure_str = ""
    for item in project_structure:
        project_structure_str += f"{'  ' * level}- {item.name}"
        if item.is_folder:
            project_structure_str += "/\n"
        else:
            project_structure_str += "\n"
        if item.is_folder:
            project_structure_str += get_project_structure_str(item.children, level + 1)
    return project_structure_str


def get_contents_str(project_structure: list[FileOrFolder], folder: str | None = None) -> str:
    contents_str = ""
    for item in project_structure:
        if not item.is_folder:
            if folder is None:
                contents_str += f"- {item.name}:\n"
            else:
                contents_str += f"- {folder}/{item.name}:\n"
            contents_str += f"Descripción: {item.description}\n"
            # Check if exists the associated file
            if folder is None:
                file_path = Path(item.name)
            else:
                file_path = Path(folder) / item.name
            if file_path.exists():
                contents_str += "Estado: Hecho, el código fue una respuesta tuya en el historial de mensajes\n"
            else:
                contents_str += "Estado: Aún no programado\n"
        else:
            contents_str += get_contents_str(item.children, item.name)
    return contents_str


async def create_project(project_structure: list[FileOrFolder], message: discord.Message, ctx: commands.Context, folder: Path, main: bool) -> None:
    folder.mkdir(exist_ok=True)
    project_messages = message_history.projects_messages
    for item in project_structure:
        if item.is_folder:
            folder_path = folder / item.name
            folder_path.mkdir(exist_ok=True)
            await create_project(item.children, message, ctx, folder_path, False)
        else:
            file_path = folder / item.name
            project_structure_str = get_project_structure_str(project_structure)
            contents_str = get_contents_str(project_structure)
            project_messages.append({"role": "user", "content": f"Problema:\n{message.content}\n\nDescripción del código que debes hacer ahora:\n{item.description}\n\nEstructura actual del proyecto:\n{project_structure_str}\n\nContenidos de los archivos programados hasta ahora:\n{contents_str}"})
            response = client.beta.chat.completions.parse(
                messages=[{"role": "system", "content": "Recibirás el problema a resolver en Python, la descripción de lo que debe hacer el archivo en particular, la estructura del proyecto con carpetas y archivos, y los archivos listos hasta ahora, cuyo contenido fue una respuesta tuya en el historial de mensajes. Debes responder con el código Python que resuelve el problema y que cumple con la descripción dada, pero considerando que hay una estructura de proyecto y debes sí o sí importar contenido de otros archivos si es necesario, aunque si hay archivos sin programar aún que son parte de la estructura, pero a la vez al módulo se le atribuye aquella funcionalidad, debes importar de ahí los objetos correspondientes con un nombre arbitrario que se te ocurra, pero que tenga sentido, es decir, que sea descriptivo. El código que resulte jamás debes resaltarlo con Markdown ni ningún texto acompañando, solo debe ir código. Si es fácil de entender el código, no comentes, solo hazlo cuando una parte del código es muy compleja. Recuerda que el problema puede cambiar, y eso quiere decir que hay un nuevo proyecto, quizás como correción del anterior, o uno completamente nuevo."}, *project_messages],
                model="gpt-4o-2024-08-06",
                response_format=Code
            )
            code = response.choices[0].message.parsed.code
            with open(file_path, "w") as fp:
                fp.write(code)
            project_messages.append({"role": "assistant", "content": response.choices[0].message.content, "parsed": {"code": code}})
    if main:
        make_archive("project", "zip", folder)
        zip_path = "project.zip"
        await ctx.send("Aquí tienes tu proyecto de programación:", file=discord.File(open(zip_path, "rb")), reference=message)
        rmtree(folder)


async def get_programming_response(message: discord.Message, ctx: commands.Context) -> None:
    python_messages = message_history.programming_messages
    python_messages.append({"role": "user", "content": message.content})
    response = client.beta.chat.completions.parse(
        messages=[
            {"role": "system", "content": "Debes responder con una estructura de proyecto de programación, en el lenguaje que se te especifique o que sea más adecuado, que resuelva el problema planteado en el mensaje, de forma recursiva, si es necesario, es decir, que las carpetas contengan archivos o carpetas, y así sucesivamente. Si el mensaje no plantea un problema, la estructura debe estar vacía."},
            *python_messages
        ],
        model="gpt-4o-2024-08-06",
        response_format=Proyect
    )
    if not response.choices[0].message.parsed.project_structure:
        return
    project_structure = response.choices[0].message.parsed.project_structure
    await create_project(project_structure, message, ctx, Path("project"), True)


def get_pods_data(pods: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    text_results = []
    image_results = []
    if len(pods) == 1 and not pods[0]:
        pods = []
    for pod in pods:
        title = pod.get("title")
        plaintext = pod.get("plaintext")
        image = pod.get("img")
        if plaintext and title:
            text_results.append(f"{title}\n{plaintext}")
        elif plaintext:
            text_results.append(plaintext)
        else:
            text_results.append(title)
        if image:
            src = image.get("src")
            if not src:
                continue
            image_results.append(src)
        subpods = pod.get("subpods") or [pod.get("subpod")]
        if len(subpods) == 1 and not subpods[0]:
            subpods = []
        sub_text_results, sub_image_results = get_pods_data(subpods)
        text_results.extend(sub_text_results)
        image_results.extend(sub_image_results)
    return text_results, image_results


async def get_math_response(input_message: discord.Message, ctx: commands.Context) -> None:
    imgs = await get_images(input_message)
    imgs = [{"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_data}"}} for content_type, image_data in imgs]
    content = input_message.content
    if imgs:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "Solo debes transcribir a texto LaTeX las imágenes que se te pasen, sin resolver nada."},
                {"role": "user", "content": [{"type": "text", "text": "Transcribe a LaTeX el contenido de las imágenes, por favor."}, *imgs]}
            ]
        )
        latex = response.choices[0].message.content
        content += f"\n\nContenido de las imágenes en LaTeX:\n{latex}"
    message_history.math_messages.append({"role": "user", "content": content})
    response = client.chat.completions.create(
        model="o1-mini",
        messages=message_history.math_messages
    )
    if not response.choices[0].message.content:
        return
    print(f"[TheMathGuysBot]: {response.choices[0].message.content}")
    message_history.math_messages.append({"role": "assistant", "content": response.choices[0].message.content})
    content = response.choices[0].message.content
    content = content.replace("\\[", "$$").replace("\\]", "$$").replace("\\(", "$").replace("\\)", "$")
    # Make sure that the LaTeX is in a single line
    regex = re.compile(r"(\$\$.*?\$\$|\$.*?\$)", re.DOTALL)
    content = regex.sub(lambda match: match.group().replace("\n", ""), content)
    with open("math.md", "w", encoding="utf-8") as fp:
        fp.write(content)
    subprocess.run(["node", "md2html.js"])
    with open("math.html", "r", encoding="utf-8") as fp:
        html = fp.read()
    story = pymupdf.Story(html=html)
    writer = pymupdf.DocumentWriter("math.pdf")
    MEDIABOX = pymupdf.paper_rect("letter")  # output page format: Letter
    WHERE = MEDIABOX + (36, 36, -36, -36)  # leave borders of 0.5 inches
    more = 1

    while more:
        device = writer.begin_page(MEDIABOX)
        more, _ = story.place(WHERE)
        story.draw(device)
        writer.end_page()

    writer.close()

    images = []
    pdf = pymupdf.open("math.pdf")
    for page in pdf:
        pix = page.get_pixmap()
        filename = f"page-{page.number}.png"
        pix.save(filename)
        images.append(filename)
    pdf.close()

    await ctx.send("Aquí tienes la solución al problema planteado:", files=[discord.File(image) for image in images], reference=input_message)


async def get_research_response(message: discord.Message, ctx: commands.Context) -> None:
    CX = os.getenv("CX")
    API_KEY = os.getenv("GOOGLE_API_KEY")
    response = client.beta.chat.completions.parse(
        messages=[
            {"role": "system", "content": "Debes responder con una consulta que se debe hacer en internet, no con la respuesta en sí."},
            {"role": "user", "content": message.content}
        ],
        model="gpt-4o-2024-08-06",
        response_format=WebQuery
    )
    query = response.choices[0].message.parsed.query
    print(f"Query: {query}")
    service = build("customsearch", "v1", developerKey=API_KEY)
    result = service.cse().list(q=query, cx=CX).execute()
    pprint.pprint(result)
    items = result.get("items", [])
    if not items:
        return
    items = [(item["link"], item["title"]) for item in items]
    paginator = ResearchPaginator(message, items, query)
    await paginator.send(ctx, target=message.channel, reference=message)


async def premium_handle_message(message: discord.Message, ctx: commands.Context) -> None:
    BOT_USER_ID = message_history.BOT_USER_ID
    premium_messages = message_history.premium_messages
    if message.author.bot:
        return
    await get_images(message)
    mentions_ids = [mention.id for mention in message.mentions]
    if BOT_USER_ID not in mentions_ids and "bot" not in message.content.lower():
        return
    premium_messages.append({"role": "user", "content": f"{message.author.mention} \"{message.content}\""})
    response = client.beta.chat.completions.parse(
        messages=[
            {"role": "system", "content": f"Debes determinar si es necesario responder al mensaje y qué tipo de respuesta se debe dar, dependiendo de lo que diga. Si es necesario responder, es decir, te mencionan con la palabra 'bot' o con <@{BOT_USER_ID}>, la respuesta debe ser 'yes'. Si no es necesario responder, la respuesta debe ser 'no'. Si el mensaje pide resolver un problema matemático, la respuesta debe ser 'solve_math'. Si te mencionan y es una conversación general, la respuesta debe ser 'general_answer'. Si te piden investigar en internet, la respuesta debe ser 'research'. Si te piden realizar un programa en Python, la respuesta debe ser 'programming_project'."},
            *premium_messages
        ],
        model="gpt-4o-2024-08-06",
        response_format=PremiumClassifier
    )
    necessary_answer = response.choices[0].message.parsed.necessary_answer
    type_ = response.choices[0].message.parsed.type
    print(f"Necessary answer: {necessary_answer}")
    print(f"Type: {type_}")
    if necessary_answer == "no":
        premium_messages.append({"role": "assistant", "content": response.choices[0].message.content, "parsed": {"necessary_answer": necessary_answer, "type": type_}})
        return
    premium_messages.append({"role": "assistant", "content": response.choices[0].message.content, "parsed": {"necessary_answer": necessary_answer, "type": type_}})
    if type_ == "solve_math":
        await get_math_response(message, ctx)
        return
    if type_ == "research":
        await get_research_response(message, ctx)
        return
    if type_ == "programming_project":
        await get_programming_response(message, ctx)
        return
    await handle_message(message)
