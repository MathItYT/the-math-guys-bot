from discord import Message
from typing import Final, Any
import google.generativeai as genai
import os
from PIL import Image
from io import BytesIO


MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
GOOGLE_API_KEY: Final[str] = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro-vision")
messages: list[dict[str, Any]] = []


async def get_images(message: Message) -> list[Image.Image]:
    images: list[Image.Image] = []
    if len(message.attachments) > 0:
        for attachment in message.attachments:
            if attachment.height is not None:
                images.append(Image.open(BytesIO(await attachment.read())))
    return images


def free_memory() -> None:
    global messages
    if len(messages) >= 100:
        del messages[0]


def generate_response(message: str, images: list[Image.Image]) -> str:
    global messages
    messages.append({"role": "user", "parts": [message, *images]})
    response = model.generate_content(messages)
    try:
        response.text
    except AttributeError:
        return "Ha ocurrido un error al generar la respuesta."
    messages.append({"role": "model", "parts": [response.text]})
    free_memory()
    return response.text


async def handle_message(message: Message) -> None:
    if BOT_USER_ID in [user.id for user in message.mentions]:
        images = await get_images(message)
        response: str = generate_response(message.content.replace(f"<@{BOT_USER_ID}>", ""), images)
        await message.channel.send(response)
