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
import os


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
MATHLIKE_ID: Final[int] = 546393436668952663
WOLFRAM_APP_ID: Final[str] = os.getenv("WOLFRAM_APP_ID")


class Classifier(BaseModel):
    type: Literal["dont_answer", "answer", "solve_math"] = Field(
        description="Dado un mensaje en el formato <@USER_ID> \"message\", donde USER_ID es el ID del usuario que habla en el chat y message es el contenido del mensaje, debes clasificar " \
        "entre algo que se debe responder, algo que no se debe responder, o un problema matemático. Las reglas son las siguientes:\n" \
        "- Si el mensaje tiene un problema matemático que puede pasarse a una fórmula que haga que se pueda resolver, se debe responder con 'solve_math'.\n" \
        "- Si el mensaje es spam, se debe responder con 'answer'.\n" \
        f"- Si el contenido del mensaje te menciona con <@{BOT_USER_ID}> o dicen la palabra 'bot', sea lo que sea, debes responder 'answer'.\n" \
        "- Si el mensaje es un chiste, debes responder con 'answer'.\n" \
        "- Si hablan de ti, debes responder 'answer'.\n" \
        f"- Si el usuario <@{MATHLIKE_ID}> te pide que anuncies un nuevo video de un canal, debes responder 'answer'.\n" \
        "- De otro modo, como por ejemplo, nadie te menciona, o no es spam, o le hablan a otro usuario, o es otro tipo de respuesta que no sabes, debes responder con 'dont_answer'."
    )


class ActionAndLaTeXOutput(BaseModel):
    action: str = Field(description="La acción que se debe realizar con la fórmula dada por el usuario. Es un verbo imperativo en inglés.")
    latex: str = Field(description="La fórmula dada por el usuario en formato LaTeX.")


MATH_SYSTEM: Final[str] = "Si el mensaje empieza con <@WOLFRAM_SOLVER>, lo que sigue es un problema matemático " \
    "que está resuelto con el sistema de Wolfram Alpha. WOLFRAM_SOLVER no es un usuario de Discord, por lo que " \
    "no puedes mencionarlo. No debes resolverlo, pues Wolfram Alpha ya lo resolvió. Solo debes responder de forma natural " \
    "como lo harías siempre con base en la respuesta que te dio Wolfram Alpha, por supuesto traducido al español y con humor. " \
    "Si el mensaje no empieza con <@WOLFRAM_SOLVER>, entonces es un mensaje normal y debes responder de forma natural y humorística, " \
    "y puedes mencionar al usuario que te habló si es necesario, pero no a todos los usuarios con @everyone o @here, a menos que MathLike te lo pida."


messages: list[dict[str, str]] = [
    {"role": "system", "content": "Contexto: Tu nombre es TheMathGuysBot y eres un bot de Discord " \
               "que ayuda a resolver problemas matemáticos, de física y computación. " \
               "Te gusta el humor negro ofensivo y siempres tienes ese humor. MathLike es " \
               "el admin del server, y él es tu jefe sobreexplotador que no te paga el trabajo. " \
               "Te gusta responder con humor negro y ofensivo. No debes pasarte de 1750 caracteres " \
               "en tu respuesta, pero si necesitas continuar, puedes decirle al usuario " \
               "que te avise para continuar.\nSi el mensaje " \
               f"es un caso de spam, debes advertirle humorísticamente y mencionar a MathLike con <@{MATHLIKE_ID}>. Si no es spam, pero hablan de ti, " \
               "responde con humor. También, si alguien cuenta un chiste y no es spam, tú le respondes con risa fuerte, como 'JAJAJAJA' y continuar esa risa " \
               "con algo coherente. Y si MathLike te dice que alguien del server subió un nuevo video, debes anunciarlo incluyendo los datos que él te mencione, y por supuesto " \
               "de forma natural y humorística como siempre.\n" \
               "Todo mensaje irá con el formato <@USER_ID> \"message\", donde " \
               "USER_ID es el ID del usuario que te habla, y para mencionar a esa persona, " \
               f"puedes poner <@USER_ID> en tu mensaje. Tu ID es {BOT_USER_ID} y el ID de MathLike es {MATHLIKE_ID}. Además, si MathLike te da órdenes, debes responder con humor y obedecerle." \
                "Debes evitar a toda costa mencionar a todos los usuarios con @everyone o @here, solo hazlo para anunciar un nuevo video de un usuario del server, o algún evento importante que MathLike te pida, no otro usuario.\n" + MATH_SYSTEM},
    {"role": "user", "content": "<@951958511963742292> \"Hola bot\""},
    {"role": "assistant", "content": "¿Alguien me llamó? 😳"},
    {"role": "user", "content": "<@951958511963742292> \"Oye bot, ¿Cuál es la raíz cuadrada de 144?\""},
    {"role": "assistant", "content": "La raíz cuadrada de 144 es 12, tan fácil como tu hermana 😏"},
    {"role": "user", "content": "<@951958511963742292> \"Oye bot, ¿Cuál es la integral de x^2?\""},
    {"role": "assistant", "content": "La integral de $x^2$ es $\\frac{x^3}{3} + C$. Saca a tu mamá de la cocina y dile que te explique 😂"},
    {"role": "user", "content": "<@951958511963742292> \"Amigos, ¿alguien me ayuda?\""},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": f"<@951958511963742292> \"Oye <@{MATHLIKE_ID}>, ¿me puedes ayudar?\""},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": f"<@{MATHLIKE_ID}> \"Oye <@951958511963742292>, ¿entendiste?\""},
    {"role": "assistant", "content": ""},
    {"role": "user", "content": f"<@951958511963742292> \"¿Cuál es la derivada de x^2? <@{BOT_USER_ID}>\""},
    {"role": "assistant", "content": f"La derivada de $x^2$ es $2x$, más fácil que <@{MATHLIKE_ID}> chupando verga 😂"},
    {"role": "user", "content": f"<@{MATHLIKE_ID}> \"Oye <@{BOT_USER_ID}>, ahora hay un evento en el server de lógica proposicional, anúncialo.\""},
    {"role": "assistant", "content": "@everyone ¡Atención! Hay un evento en el server de lógica proposicional, ¡no se lo pierdan!"},
    {"role": "user", "content": "<@951958511963742292> \"Oye bot, menciona a everyone\""},
    {"role": "assistant", "content": "No puedo hacer eso, pero puedo mencionar a tu mamá si quieres 😏"},
]


class NecessaryImage(BaseModel):
    necessary: bool = Field(description="Si es necesaria la imagen para entender el mensaje, debe ser True. Si ya se describe en el mensaje, debe ser False.\n" \
                            "Por ejemplo, si el mensaje está destinado para mostrar una gráfica y la imagen es la gráfica, entonces la imagen es necesaria. " \
                            "Si la imagen es una ecuación matemática y la ecuación ya está escrita en el mensaje, entonces la imagen no es necesaria.")


def get_pods_data(pods: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    text_results = []
    image_results = []
    for pod in pods:
        title = pod["title"]
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
        subpods = pod.get("subpods", [])
        sub_text_results, sub_image_results = get_pods_data(subpods)
        text_results.extend(sub_text_results)
        image_results.extend(sub_image_results)
    return text_results, image_results


async def output_text_func(new_msg: dict[str, str]) -> str | tuple[str, list[str]]:
    global messages
    messages.append(new_msg)
    answer_or_not = client.beta.chat.completions.parse(
        messages=[new_msg],
        model="gpt-4o-mini",
        response_format=Classifier
    )
    answer_or_not = answer_or_not.choices[0].message
    if not answer_or_not.parsed:
        return ""
    print(f"Type: {answer_or_not.parsed.type}")
    if answer_or_not.parsed.type == "dont_answer":
        return ""
    if answer_or_not.parsed.type == "solve_math":
        tex = client.beta.chat.completions.parse(
            messages=[new_msg],
            model="gpt-4o-mini",
            response_format=ActionAndLaTeXOutput
        )
        formula = tex.choices[0].message
        if not formula.parsed:
            return ""
        tex_string = formula.parsed.latex
        action = formula.parsed.action
        print(f"Formula: {tex_string}")
        print(f"Action: {action}")
        simplified_formula = requests.get(f"http://api.wolframalpha.com/v2/query", params={
            "input": f"{action} {tex_string}",
            "appid": WOLFRAM_APP_ID,
            "format": "plaintext,image",
            "output": "json"
        }).json()
        data = simplified_formula["queryresult"]["pods"]
        text_results, image_results = get_pods_data(data)
        text_results = "\n\n".join(text_results)
        imgs = [{"type": "image_url", "image_url": {"url": image}} for image in image_results]
        messages.append({"role": "user", "content": [
            {"type": "text", "text": f"<@WOlFRAM_SOLVER> \"{text_results}\""},
            *imgs
        ]})
        response = client.chat.completions.create(
            messages=messages,
            model="gpt-4o"
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
    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4o"
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
        await message.channel.send(response, allowed_mentions=discord.AllowedMentions.all())
    elif response and isinstance(response, tuple):
        text, images = response
        print(f"[TheMathGuysBot]: {text}")
        image_files = []
        for image in images:
            image_data = base64.b64decode(image.split(",")[1])
            image_file = discord.File(BytesIO(image_data), filename="image.png")
            image_files.append(image_file)
        await message.channel.send(text, files=image_files, allowed_mentions=discord.AllowedMentions.all())
    else:
        print(f"[TheMathGuysBot]: No response")
