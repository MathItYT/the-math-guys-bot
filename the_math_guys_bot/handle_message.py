from discord import Message
from typing import Final, Optional
import google.generativeai as genai
import google.ai.generativelanguage as glm
from pathlib import Path
import os


MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
GOOGLE_API_KEY: Final[str] = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model1 = genai.GenerativeModel("gemini-pro-vision")
model2 = genai.GenerativeModel("gemini-pro")


async def save_image(message: Message) -> Optional[bytes]:
    for attachment in message.attachments:
        if attachment.content_type.startswith("image"):
            with open(f"temp{Path(attachment.filename).suffix}", "wb") as f:
                await attachment.save(f)
            return Path(f"temp{Path(attachment.filename).suffix}").read_bytes()
    return None

def generate_response(message: str, image: Optional[bytes]) -> str:
    if image is not None:
        response = model1.generate_content(
            glm.Content(
                parts=[
                    glm.Part(text=message),
                    glm.Part(
                        inline_data=glm.Blob(
                            mime_type="image/png",
                            data=image
                        )
                    )
                ]
            )
        )
    else:
        response = model2.generate_content(
            glm.Content(
                parts=[
                    glm.Part(text=message)
                ]
            )
        )
    try:
        response.parts[0].text
    except ValueError:
        return "Ha ocurrido un error al generar la respuesta."
    return response.parts[0].text


async def handle_message(message: Message) -> None:
    if BOT_USER_ID in [user.id for user in message.mentions]:
        image = await save_image(message)
        response: str = generate_response(message.content.replace(f"<@{BOT_USER_ID}>", ""), image)
        await message.channel.send(response)
