from discord import Message
from typing import Final
from vertexai.preview.generative_models import GenerativeModel, Image


MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
model = GenerativeModel("gemini-pro-vision")
chat = model.start_chat()


async def get_images(message: Message) -> list[Image]:
    images: list[Image] = []
    if len(message.attachments) > 0:
        for attachment in message.attachments:
            if attachment.height is not None:
                images.append(Image.from_bytes(await attachment.read()))
    return images


def generate_response(message: str, images: list[Image]) -> str:
    response = chat.send_message(images + [message])
    return response.text


async def handle_message(message: Message) -> None:
    if BOT_USER_ID in [user.id for user in message.mentions]:
        images = await get_images(message)
        response: str = generate_response(message.content.replace(f"<@{BOT_USER_ID}>", ""), images)
        await message.channel.send(response)
