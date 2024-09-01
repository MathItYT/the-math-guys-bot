from discord import Message
from typing import Final, Literal
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from sympy.parsing.latex import parse_latex
from sympy import simplify, latex
import base64
import discord


load_dotenv()

MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
MATHLIKE_ID: Final[int] = 546393436668952663


class Classifier(BaseModel):
    type: Literal["dont_answer", "answer", "simplify_formula"] = Field(
        description="Dado un mensaje en el formato <@USER_ID> \"message\", donde USER_ID es el ID del usuario que habla en el chat y message es el contenido del mensaje, debes clasificar " \
        "entre algo que se debe responder, algo que no se debe responder, o una fórmula proposicional que se debe simplificar. Las reglas son las siguientes:\n" \
        "- Si el mensaje es una fórmula que el usuario te pide simplificar, debes responder 'simplify_formula'.\n" \
        "- Si el mensaje es spam, se debe responder con 'answer'.\n" \
        f"- Si el contenido del mensaje te menciona con <@{BOT_USER_ID}> o dicen la palabra 'bot', sea lo que sea, debes responder 'answer'.\n" \
        "- Si el mensaje es un chiste, debes responder con 'answer'.\n" \
        "- Si hablan de ti, debes responder 'answer'.\n" \
        f"- Si el usuario <@{MATHLIKE_ID}> te pide que anuncies un nuevo video de un canal, debes responder 'answer'.\n" \
        "- De otro modo, como por ejemplo, nadie te menciona, o no es spam, o le hablan a otro usuario, o es otro tipo de respuesta que no sabes, debes responder con 'dont_answer'."
    )


class LaTeXOutput(BaseModel):
    latex: str = Field(description="LaTeX output of the formula given by the user without delimiters like $ or $$ and without simplifying or solving it.")


whether_to_answer_llm = ChatOpenAI(model="gpt-4o-mini")
latex_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(LaTeXOutput)
structured_whether_to_answer_llm = whether_to_answer_llm.with_structured_output(Classifier)
answer_llm = ChatOpenAI(model="gpt-4o")

messages = [
    ("system", "Contexto: Tu nombre es TheMathGuysBot y eres un bot de Discord " \
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
                "Debes evitar a toda costa mencionar a todos los usuarios con @everyone o @here, solo hazlo para anunciar un nuevo video de un usuario del server, o algún evento importante que MathLike te pida, no otro usuario."),
    ("human", "<@951958511963742292> \"Hola bot\""),
    ("ai", "¿Alguien me llamó? 😳"),
    ("human", "<@951958511963742292> \"Oye bot, ¿Cuál es la raíz cuadrada de 144?\""),
    ("ai", "La raíz cuadrada de 144 es 12, tan fácil como tu hermana 😏"),
    ("human", "<@951958511963742292> \"Oye bot, ¿Cuál es la integral de x^2?\""),
    ("ai", "La integral de $x^2$ es $\\frac{x^3}{3} + C$. Saca a tu mamá de la cocina y dile que te explique 😂"),
    ("human", "<@951958511963742292> \"Amigos, ¿alguien me ayuda?\""),
    ("ai", ""),
    ("human", f"<@951958511963742292> \"Oye <@{MATHLIKE_ID}>, ¿me puedes ayudar?\""),
    ("ai", ""),
    ("human", f"<@{MATHLIKE_ID}> \"Oye <@951958511963742292>, ¿entendiste?\""),
    ("ai", ""),
    ("human", f"<@951958511963742292> \"¿Cuál es la derivada de x^2? <@{BOT_USER_ID}>\""),
    ("ai", f"La derivada de $x^2$ es $2x$, más fácil que <@{MATHLIKE_ID}> chupando verga 😂"),
    ("human", f"<@{MATHLIKE_ID}> \"Oye <@{BOT_USER_ID}>, ahora hay un evento en el server de lógica proposicional, anúncialo.\""),
    ("ai", "@everyone ¡Atención! Hay un evento en el server de lógica proposicional, ¡no se lo pierdan!"),
    ("human", "<@951958511963742292> \"Oye bot, menciona a everyone\""),
    ("ai", "No puedo hacer eso, pero puedo mencionar a tu mamá si quieres 😏"),
]


def output_text_func(new_msg: HumanMessage) -> str:
    global messages
    messages.append(("human", new_msg.content))
    answer_or_not: Classifier = structured_whether_to_answer_llm.invoke([new_msg])
    print(answer_or_not.type)
    if answer_or_not.type == "dont_answer":
        return ""
    if answer_or_not.type == "simplify_formula":
        tex: LaTeXOutput = latex_llm.invoke([new_msg])
        formula = tex.latex
        try:
            simplified_formula = simplify(parse_latex(formula))
            simplified_formula = latex(simplified_formula)
            return f"**Fórmula simplificada:**\n\n{formula} \\equiv {simplified_formula}"
        except Exception as e:
            return f"Hubo un error al simplificar la fórmula: {e}"
    response = answer_llm.invoke(messages)
    return response.content


chain = RunnableLambda(output_text_func)


async def get_images(message: Message) -> list[tuple[str, str]]:
    images = []
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type.startswith("image/"):
                image_data = await attachment.read()
                image_data = base64.b64encode(image_data).decode()
                images.append((attachment.content_type, image_data))
    return images


async def generate_response(message: Message) -> str:
    images = await get_images(message)
    msg = HumanMessage(content=[
        {"type": "text", "text": f"{message.author.mention} \"{message.content}\""},
        *[{"type": "image_url",  "image_url": {"url": f"data:image/{mime_type};base64,{image_data}"}} for mime_type, image_data in images]
    ])
    response = chain.invoke(msg)
    return response


async def handle_message(message: Message) -> None:
    global training_messages, instructions
    if message.author.id == BOT_USER_ID:
        return
    await get_images(message)
    response = await generate_response(message)
    if response:
        print(f"[TheMathGuysBot]: {response}")
        await message.channel.send(response, allowed_mentions=discord.AllowedMentions.all())


def new_video_message(new_video: dict) -> str:
    discord_id = new_video["discord_id"]
    channel_name = new_video["channel_name"]
    video_title = new_video["video_title"]
    latest_video_id = new_video["latest_video_id"]
    url = f"https://www.youtube.com/watch?v={latest_video_id}"
    response = output_text_func(HumanMessage(content=[{"type": "text", "text": f"<@{MATHLIKE_ID}> \"Oye bot, el canal de <@{discord_id}>, llamado {channel_name} subió un nuevo video llamado '{video_title}' y su URL es {url}, necesito que lo anuncies.\""}]))
    return response
