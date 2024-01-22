from discord import Message
from typing import Final, Any
import google.generativeai as genai
import google.ai.generativelanguage as glm
import os
from PIL import Image
from io import BytesIO


MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
GOOGLE_API_KEY: Final[str] = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro-vision")


async def get_images(message: Message) -> list[Image.Image]:
    images: list[Image.Image] = []
    for attachment in message.attachments:
        if attachment.content_type.startswith("image"):
            images.append(Image.open(BytesIO(await attachment.read())))
    return images


def generate_response(message: str, images: list[Image.Image]) -> str:
    response = model.generate_content(
        glm.Content(
            parts=[
                glm.Part(text=message),
                glm.Part(
                    inline_data=glm.Blob(
                        mime_type="image/png",
                        data=images[0].tobytes()
                    )
                )
            ]
        )
    )
    try:
        response.text
    except AttributeError:
        return "Ha ocurrido un error al generar la respuesta."
    return response.text


async def handle_message(message: Message) -> None:
    if BOT_USER_ID in [user.id for user in message.mentions]:
        images = await get_images(message)
        response: str = generate_response(message.content.replace(f"<@{BOT_USER_ID}>", ""), images)
        await message.channel.send(response)
