from discord import Message
from typing import Literal
from dotenv import load_dotenv
import base64
from pydantic import BaseModel, Field
import discord
from io import BytesIO
import requests
from PIL import Image
import manim
import traceback
import sys
import random
import math
from pathlib import Path
from shutil import rmtree
from the_math_guys_bot import message_history


load_dotenv()


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


class NecessaryImage(BaseModel):
    necessary: Literal["yes", "no"] = Field(description="Si es necesaria la imagen para entender el mensaje, debe ser 'yes'. Si ya se describe en el mensaje, debe ser 'no'.\n" \
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
    client = message_history.client
    messages = message_history.messages
    training_messages = message_history.training_messages
    prompt = f"<@MEMBER_JOIN> \"{member.mention} se ha unido al servidor. Dale la bienvenida.\""
    prompt = {"role": "user", "content": prompt}
    messages.append(prompt)
    response = client.chat.completions.create(
        messages=training_messages + messages,
        model="gpt-4o-2024-08-06",
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
    MAX_MESSAGES_LENGTH = message_history.MAX_MESSAGES_LENGTH
    client = message_history.client
    WOLFRAM_APP_ID = message_history.WOLFRAM_APP_ID
    messages = message_history.messages
    math_messages = message_history.math_messages
    manim_messages = message_history.manim_messages
    classifier_messages = message_history.classifier_messages
    propositional_logic_1_messages = message_history.propositional_logic_1_messages
    training_messages = message_history.training_messages
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
        messages=[
            {"role": "system", "content": "Debes determinar si debes responder al mensaje o no y el tipo de respuesta. Si el mensaje no dice la palabra 'bot' ni <@BOT_USER_ID>, no te están mencionando ni refiriéndose a ti, y si además de eso, no hay spam, la respuesta no es necesaria y necessary_answer debe ser 'no' obligatoriamente, pero si se dirigen a ti o hay spam, ahí debe ser necessary_answer 'yes'. Si se habla del curso de lógica 1, debes responder con type siendo 'propositional_logic_1'. Si se pide resolver un problema matemático general, debes responder con type siendo 'solve_math'. Si se te pide una animación de Manim, debes responder con type siendo 'manim_animation'. Si te mencionan y es una conversación general, debes responder con type siendo 'general_answer'."},
            *classifier_messages
        ],
        model="gpt-4o-2024-08-06",
        response_format=message_history.Classifier
    )
    answer_or_not = answer_or_not.choices[0].message
    if not answer_or_not.parsed:
        return ""
    print(f"Type: {answer_or_not.parsed.type}")
    print(f"Necessary answer: {answer_or_not.parsed.necessary_answer}")
    classifier_messages.append({"role": "assistant", "parsed": {"type": answer_or_not.parsed.type, "necessary_answer": answer_or_not.parsed.necessary_answer}, "content": answer_or_not.content})
    if answer_or_not.parsed.necessary_answer == "no":
        return ""
    if answer_or_not.parsed.type == "solve_math":
        math_messages.append(new_msg)
        tex = client.beta.chat.completions.parse(
            messages=math_messages,
            model="gpt-4o-2024-08-06",
            response_format=ActionAndPrintableOutput
        )
        formula = tex.choices[0].message
        if not formula.parsed:
            return ""
        printable_string = formula.parsed.printable_math
        action = formula.parsed.action
        print(f"Formula: {printable_string}")
        print(f"Action: {action}")
        math_messages.append({"role": "assistant", "parsed": {"printable_math": printable_string, "action": action}, "content": formula.content})
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
            model="gpt-4o-2024-08-06",
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
                    model="gpt-4o-2024-08-06",
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
            {"type": "text", "text": f"<@PROPOSITIONAL_LOGIC_1> \"{message_content}\n\nRecuerda responder con humor y naturalidad, y copiar exactamente lo que dice el profesor, pero con tu estilo humorístico, y sin LaTeX, además de respetar el límite de 1000 caracteres.\""}
        ]})
        response = client.chat.completions.create(
            messages=training_messages + messages,
            model="gpt-4o-2024-08-06",
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
        manim_messages.append({"role": "assistant", "parsed": {"code": code.parsed.code}, "content": code.content})
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
                manim_messages.append({"role": "assistant", "parsed": {"code": code.parsed.code}, "content": code.content})
        media_dir = Path("media")
        media_files = get_media_files_recursively(media_dir)
        messages.append({"role": "user", "content": f"<@MANIM> \"{code.parsed.code}\""})
        response = client.chat.completions.create(
            messages=training_messages + messages,
            model="gpt-4o-2024-08-06",
            max_tokens=400
        )
        if response.choices[0].message.content:
            return response.choices[0].message.content, media_files
        return ""
    response = client.chat.completions.create(
        messages=training_messages + messages,
        model="gpt-4o-2024-08-06",
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
    message_history.messages.clear()
    message_history.math_messages.clear()
    message_history.manim_messages.clear()
    message_history.classifier_messages.clear()
    message_history.propositional_logic_1_messages.clear()


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
    BOT_USER_ID = message_history.BOT_USER_ID
    messages = message_history.messages
    if message.author.bot:
        return
    await get_images(message)
    mentions_ids = [mention.id for mention in message.mentions]
    if BOT_USER_ID not in mentions_ids and "bot" not in message.content.lower():
        messages.append({"role": "user", "content": f"{message.author.mention} \"{message.content}\""})
        return
    response = await generate_response(message)
    if response and isinstance(response, str):
        print(f"[TheMathGuysBot]: {response}")
        if len(response) > 2000:
            response = response[:2000]
        await message.reply(content=response, allowed_mentions=discord.AllowedMentions.all())
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
