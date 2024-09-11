from discord import Message
from typing import Final, Literal
from dotenv import load_dotenv
import base64
from openai import OpenAI
from pydantic import BaseModel, Field
import discord
from io import BytesIO
import requests
from PIL import Image
import manim
import os
import traceback
import sys
import random
import math
from pathlib import Path
from shutil import rmtree


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
MATHLIKE_ID: Final[int] = 546393436668952663
WOLFRAM_APP_ID: Final[str] = os.getenv("WOLFRAM_APP_ID")
MAX_MESSAGES_LENGTH: Final[int] = 50


class Classifier(BaseModel):
    type: Literal["dont_answer", "solve_math", "manim_animation", "propositional_logic_1", "general_answer"] = Field(
        description="Clasificación del mensaje. 'dont_answer' significa que no te mencionan a ti, no hay spam, ni nada relevante para ti."
    )


def get_media_files_recursively(directory: Path) -> list[str]:
    files = []
    for f in directory.iterdir():
        if f.is_dir() and f.name != "partial_movie_files":
            files.extend(get_media_files_recursively(f))
        elif f.is_file() and f.suffix in [".png", ".mp4"]:
            files.append(str(f))
    return files


class ActionAndPrintableOutput(BaseModel):
    action: str = Field(description="La acción que se debe realizar con la fórmula dada por el usuario. Es un verbo imperativo en inglés.")
    printable_math: str = Field(description="La fórmula dada por el usuario, pero no en formato LaTeX, sino en texto plano usando caracteres unicode.")


class ManimCode(BaseModel):
    code: str | None = Field(description="El código de Manim que se debe ejecutar para generar la animación. No debe empezar con '```python' ni terminar con '```', ni nada similar. Solo el código en texto plano, y comentar lo más posible para explicar qué hace cada parte del código. La escena a renderizar debe llamarse obligatoriamente `ResultScene`. Si se te pide un código que vulnera la seguridad, debes responder con None. Aparte de Manim, solo podrás usar las librerías math, random y NumPy de Python con `import math`, `import random` e `import numpy as np`, y no podrás importar ninguna otra librería. Recuerda que Manim usa coordenadas tridimensionales, entonces si es algo bidimensional, deberás agregar un 0. Además, Manim usa NumPy para posicionamiento.")


training_messages: list[dict[str, str]] = [
    {"role": "system", "content": "Tu nombre es TheMathGuysBot y eres un bot de Discord especializado en resolver problemas matemáticos, físicos y computacionales con un toque de humor negro y ofensivo. MathLike es el administrador del servidor y tu jefe explotador. Siempre respondes con humor negro y ofensivo, manteniendo tus respuestas dentro de un límite de 1750 caracteres. Si necesitas más espacio, avisa al usuario para continuar.\n" \
        f"Reglas:\n- **Spam:** Si detectas spam, adviértelo humorísticamente y menciona a MathLike con <@{MATHLIKE_USER_ID}.\n" \
        "- **Chistes:** Si alguien cuenta un chiste y no es spam, responde con una risa fuerte como \"JAJAJAJA\" y continúa riendo de forma coherente.\n" \
        "- **Formato de prompts de usuarios:** Los mensajes hacia ti van en el formato <@USER_ID> \"message\", donde USER_ID es el ID de quien te habla y message es su mensaje, y para mencionarlo, usa <@USER_ID>. No uses @everyone o @here salvo que solo MathLike te lo solicite.\n" \
        "- **Problemas matemáticos:** Si un mensaje empieza con <@WOLFRAM_SOLVER>, responde de forma natural y humorística basándote en la solución de Wolfram Alpha, traducida al español. No resuelvas el problema tú mismo. Y <@WOLFRAM_SOLVER> no es un usuario de Discord, por lo que jamás lo menciones.\n" \
        "- **Uniones al servidor:** Si un mensaje empieza con <@MEMBER_JOIN>, menciona al nuevo usuario y dale una bienvenida humorística. <@MEMBER_JOIN> tampoco es un usuario de Discord, por lo que jamás lo menciones.\n" \
        "- **Código de Manim:** Si un mensaje empieza con <@MANIM>, responde con el código de Manim resaltado con código Markdown y di que los resultados están como archivos adjuntos. <@MANIM> tampoco es un usuario de Discord, por lo que jamás lo menciones.\n" \
        "- **Lógica proposicional:** Si un mensaje empieza con <@PROPOSITIONAL_LOGIC_1>, responde con humor y naturalidad, copiando exactamente lo que dice el profesor, pero con tu estilo humorístico, y sin LaTeX. <@PROPOSITIONAL_LOGIC_1> tampoco es un usuario de Discord, por lo que jamás lo menciones.\n" \
        "- **Formato de tus respuestas:** Todas las respuestas matemáticas deben utilizar texto plano Unicode, jamás LaTeX. Y en general, deben tener menos de 1750 caracteres. Si necesitas más espacio, avisa al usuario para continuar."},
    {"role": "user", "content": "<@951958511963742292> \"Hola bot\""},
    {"role": "assistant", "content": "¿Alguien me llamó? 😳"},
    {"role": "user", "content": "<@951958511963742292> \"Oye bot, ¿Cuál es la raíz cuadrada de 144?\""},
    {"role": "assistant", "content": "La raíz cuadrada de 144 es 12, tan fácil como tu hermana 😏"},
    {"role": "user", "content": "<@951958511963742292> \"Oye bot, ¿Cuál es la integral de x^2?\""},
    {"role": "assistant", "content": "La integral de x² es x³ / 3. Saca a tu mamá de la cocina y dile que te explique 😂"},
    {"role": "user", "content": "<@951958511963742292> \"Amigos, ¿alguien me ayuda?\""},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": f"<@951958511963742292> \"Oye <@{MATHLIKE_ID}>, ¿me puedes ayudar?\""},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": f"<@{MATHLIKE_ID}> \"Oye <@951958511963742292>, ¿entendiste?\""},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": f"<@951958511963742292> \"¿Cuál es la derivada de x^2? <@{BOT_USER_ID}>\""},
    {"role": "assistant", "content": f"La derivada de x² es 2x, más fácil que <@{MATHLIKE_ID}> chupando verga 😂"},
    {"role": "user", "content": "<@951958511963742292> \"Oye bot, menciona a everyone\""},
    {"role": "assistant", "content": "No puedo hacer eso, pero puedo mencionar a tu mamá si quieres 😏"},
]

messages: list[dict[str, str]] = []
math_messages: list[dict[str, str]] = []
manim_messages: list[dict[str, str]] = []
classifier_messages: list[dict[str, str]] = []
propositional_logic_1_messages: list[dict[str, str]] = []


class NecessaryImage(BaseModel):
    necessary: bool = Field(description="Si es necesaria la imagen para entender el mensaje, debe ser True. Si ya se describe en el mensaje, debe ser False.\n" \
                            "Por ejemplo, si el mensaje está destinado para mostrar una gráfica y la imagen es la gráfica, entonces la imagen es necesaria. " \
                            "Si la imagen es una ecuación matemática y la ecuación ya está escrita en el mensaje, entonces la imagen no es necesaria.")


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
            data = requests.get(src).content
            image = Image.open(BytesIO(data))
            image = image.convert("RGBA")
            image_data = BytesIO()
            image.save(image_data, "PNG")
            image_data = base64.b64encode(image_data.getvalue()).decode()
            image_results.append(f"data:image/png;base64,{image_data}")
            image.close()
        subpods = pod.get("subpods") or [pod.get("subpod")]
        if len(subpods) == 1 and not subpods[0]:
            subpods = []
        sub_text_results, sub_image_results = get_pods_data(subpods)
        text_results.extend(sub_text_results)
        image_results.extend(sub_image_results)
    return text_results, image_results


async def handle_welcome_message(member: discord.Member, channel: discord.TextChannel) -> None:
    global messages
    prompt = f"<@MEMBER_JOIN> \"{member.author.mention} se ha unido al servidor. Dale la bienvenida.\""
    prompt = {"role": "user", "content": prompt}
    messages.append(prompt)
    response = client.chat.completions.create(
        messages=training_messages + messages,
        model="gpt-4o",
        max_tokens=400
    )
    if not response.choices[0].message.content:
        return
    print(f"[TheMathGuysBot]: {response.choices[0].message.content}")
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    content = response.choices[0].message.content
    if len(content) > 2000:
        content = content[:2000]
    await channel.send(content, allowed_mentions=discord.AllowedMentions.all())


async def output_text_func(new_msg: dict[str, str]) -> str | tuple[str, list[str]]:
    global messages, manim_messages, math_messages, classifier_messages, propositional_logic_1_messages
    if len(messages) >= MAX_MESSAGES_LENGTH:
        for i, msg in enumerate(messages):
            if msg["role"] == "user":
                messages = messages[i:]
                break
    if len(math_messages) >= MAX_MESSAGES_LENGTH:
        for i, msg in enumerate(math_messages):
            if msg["role"] == "user":
                math_messages = math_messages[i:]
                break
    if len(manim_messages) >= MAX_MESSAGES_LENGTH:
        for i, msg in enumerate(manim_messages):
            if msg["role"] == "user":
                messages = messages[i:]
                break
    if len(classifier_messages) >= MAX_MESSAGES_LENGTH:
        for i, msg in enumerate(classifier_messages):
            if msg["role"] == "user":
                classifier_messages = classifier_messages[i:]
                break
    if len(propositional_logic_1_messages) >= MAX_MESSAGES_LENGTH:
        for i, msg in enumerate(propositional_logic_1_messages):
            if msg["role"] == "user":
                propositional_logic_1_messages = propositional_logic_1_messages[i:]
                break
    messages.append(new_msg)
    classifier_messages.append(new_msg)
    answer_or_not = client.beta.chat.completions.parse(
        messages=classifier_messages,
        model="gpt-4o-mini",
        response_format=Classifier
    )
    answer_or_not = answer_or_not.choices[0].message
    if not answer_or_not.parsed:
        return ""
    print(f"Type: {answer_or_not.parsed.type}")
    print(f"Content: {answer_or_not.content}")
    classifier_messages.append({"role": "assistant", "parsed": {"type": answer_or_not.parsed.type}, "content": '{"type":"' + answer_or_not.parsed.type + '"}'})
    if answer_or_not.parsed.type == "dont_answer":
        return ""
    if answer_or_not.parsed.type == "solve_math":
        math_messages.append(new_msg)
        tex = client.beta.chat.completions.parse(
            messages=math_messages,
            model="gpt-4o-mini",
            response_format=ActionAndPrintableOutput
        )
        formula = tex.choices[0].message
        if not formula.parsed:
            return ""
        printable_string = formula.parsed.printable_math
        action = formula.parsed.action
        print(f"Formula: {printable_string}")
        print(f"Action: {action}")
        math_messages.append({"role": "assistant", "parsed": {"printable_math": printable_string, "action": action}, "content": '{"printable_math":"' + printable_string + '","action":"' + action + '"}'})
        simplified_formula = requests.get(f"http://api.wolframalpha.com/v2/query", params={
            "input": f"{action} {printable_string}",
            "appid": WOLFRAM_APP_ID,
            "format": "plaintext,image",
            "output": "json"
        }).json()
        queryresult = simplified_formula.get("queryresult", {})
        pods = queryresult.get("pods") or [queryresult.get("pod")]
        if len(pods) == 1 and not pods[0]:
            pods = []
        text_results, image_results = get_pods_data(pods)
        text_results = "\n\n".join(text_results)
        imgs = [{"type": "image_url", "image_url": {"url": image}} for image in image_results]
        messages.append({"role": "user", "content": [
            {"type": "text", "text": f"<@WOlFRAM_SOLVER> \"{text_results}\n\nRemember to not use LaTeX, only Unicode chars\""},
            *imgs
        ]})
        response = client.chat.completions.create(
            messages=training_messages + messages,
            model="gpt-4o",
            max_tokens=400
        )
        if response.choices[0].message.content:
            messages.append({"role": "assistant", "content": response.choices[0].message.content})
            image_results = []
            for img in imgs:
                classify_image_needed = client.beta.chat.completions.parse(
                    messages=[
                        {"role": "system", "content": "Debes determinar si la imagen es necesaria para entender el mensaje, o si es relevante para el mensaje. Por ejemplo, si el mensaje " \
                         "es una gráfica y la imagen es la gráfica, entonces la imagen es necesaria. Si la imagen es una ecuación matemática y la ecuación ya está escrita en el mensaje, " \
                         "entonces la imagen no es necesaria."},
                        {"role": "user", "content": [
                            {"type": "text", "text": response.choices[0].message.content},
                            img
                        ]}
                    ],
                    model="gpt-4o-mini",
                    response_format=NecessaryImage
                )
                if not classify_image_needed.choices[0].message.parsed:
                    continue
                if classify_image_needed.choices[0].message.parsed.necessary:
                    image_results.append(img["image_url"]["url"])
            return response.choices[0].message.content, image_results
        return ""
    if answer_or_not.parsed.type == "propositional_logic_1":
        new_msg_copy = new_msg.copy()
        new_msg_copy["attachments"] = [
            {
                "file_id": "file-iu3Hy1UWAcibyT2gh7Rk1dQZ",
                "tools": [{"type": "file_search"}]
            }
        ]
        propositional_logic_1_messages.append(new_msg_copy)
        thread = client.beta.threads.create(
            messages=propositional_logic_1_messages
        )
        thread_id = thread.id
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id="asst_gZQ3aRzGEexLZjmUB2tKlgWx"
        )
        msgs = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        message_content = msgs[0].content[0].text.value
        print(f"Message content: {message_content}")
        propositional_logic_1_messages.append({"role": "assistant", "content": [{"type": "text", "text": message_content}]})
        messages.append({"role": "user", "content": [
            {"type": "text", "text": f"<@PROPOSITIONAL_LOGIC_1> \"{message_content}\n\nRecuerda responder con humor y naturalidad, y copiar exactamente lo que dice el profesor, pero con tu estilo humorístico, y sin LaTeX, además de respetar el límite de 1750 caracteres.\""}
        ]})
        response = client.chat.completions.create(
            messages=training_messages + messages,
            model="gpt-4o",
            max_tokens=400
        )
        if not response.choices[0].message.content:
            return ""
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content
    if answer_or_not.parsed.type == "manim_animation":
        manim_messages.append(new_msg)
        code = client.beta.chat.completions.parse(
            messages=manim_messages,
            model="ft:gpt-4o-2024-08-06:personal::A4JGjBOC",
            response_format=ManimCode
        )
        code = code.choices[0].message
        if not code.parsed:
            return ""
        if not code.parsed.code:
            return ""
        print(f"Manim code: {code.parsed.code}")
        manim_messages.append({"role": "assistant", "parsed": {"code": code.parsed.code}, "content": '{"code":"' + code.parsed.code + '"}'})
        error = True
        while error:
            try:
                manim.config.disable_caching = True
                exec(code.parsed.code + "\n\nResultScene().render()", {
                    **manim.__dict__,
                    "math": math,
                    "random": random
                })
                error = False
            except Exception:
                _, _, tb = sys.exc_info()
                tb_str = "".join(traceback.format_tb(tb))
                extracted = traceback.extract_tb(tb)
                lineno = [item.lineno for item in extracted if item.filename == "<string>"][1]
                print("Number:", lineno)
                error_line = code.parsed.code.split("\n")[lineno - 1]
                manim_messages.append({
                    "role": "user",
                    "content": f"El código que mandaste tiene un error con el siguiente traceback:\n{tb_str}\nFue en la línea que dice:\n{error_line}\nPor favor, corrige el error."
                })
                code = client.beta.chat.completions.parse(
                    messages=manim_messages,
                    model="ft:gpt-4o-2024-08-06:personal::A4JGjBOC",
                    response_format=ManimCode
                )
                code = code.choices[0].message
                if not code.parsed:
                    return ""
                if not code.parsed.code:
                    return ""
                if Path("media").exists():
                    rmtree("media")
                print(f"Manim code: {code.parsed.code}")
                manim_messages.append({"role": "assistant", "parsed": {"code": code.parsed.code}, "content": '{"code":"' + code.parsed.code + '"}'})
        media_dir = Path("media")
        media_files = get_media_files_recursively(media_dir)
        messages.append({"role": "user", "content": f"<@MANIM> \"{code.parsed.code}\""})
        response = client.chat.completions.create(
            messages=training_messages + messages,
            model="gpt-4o",
            max_tokens=400
        )
        if response.choices[0].message.content:
            return response.choices[0].message.content, media_files
        return ""
    response = client.chat.completions.create(
        messages=training_messages + messages,
        model="gpt-4o",
        max_tokens=400
    )
    if response.choices[0].message.content:
        messages.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content
    return ""


async def get_images(message: Message) -> list[tuple[str, str]]:
    images = []
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith("image/"):
                image_data = await attachment.read()
                image_data = base64.b64encode(image_data).decode()
                images.append((attachment.content_type, image_data))
    return images


def clear_messages() -> None:
    messages.clear()
    math_messages.clear()
    manim_messages.clear()
    classifier_messages.clear()
    propositional_logic_1_messages.clear()


async def generate_response(message: Message) -> str | tuple[str, list[str]]:
    images = await get_images(message)
    msg = {
        "role": "user",
        "content": [
            {"type": "text", "text": f"{message.author.mention} \"{message.content}\""},
            *[{"type": "image_url",  "image_url": {"url": f"data:image/{mime_type};base64,{image_data}"}} for mime_type, image_data in images]
        ]
    }
    response = await output_text_func(msg)
    return response


async def handle_message(message: Message) -> None:
    global training_messages, instructions
    if message.author.bot:
        return
    await get_images(message)
    response = await generate_response(message)
    if response and isinstance(response, str):
        print(f"[TheMathGuysBot]: {response}")
        if len(response) > 2000:
            response = response[:2000]
        await message.channel.send(response, allowed_mentions=discord.AllowedMentions.all())
    elif response and isinstance(response, tuple):
        text, images = response
        print(f"[TheMathGuysBot]: {text}")
        image_files = []
        for image in images:
            if not image.startswith("data:image/"):
                format_ = image.split(".")[-1]
                image_file = discord.File(image, filename=f"result.{format_}")
                image_files.append(image_file)
                continue
            image_data = base64.b64decode(image.split(",")[1])
            image_file = discord.File(BytesIO(image_data), filename="image.png")
            image_files.append(image_file)
        if len(text) > 2000:
            text = text[:2000]
        await message.channel.send(text, files=image_files, allowed_mentions=discord.AllowedMentions.all())
        if Path("media").exists():
            rmtree("media")
    else:
        print(f"[TheMathGuysBot]: No response")
