from discord import Message
from openai import OpenAI
from typing import Final


MATHLIKE_USER_ID: Final[int] = 546393436668952663


def is_spam(message_content: str, client: OpenAI) -> bool:
    openai_response: str = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "Debes determinar si el mensaje es spam o no con Yes o No."},
            {"role": "user", "content": f"¿Es spam el siguiente mensaje?: {message_content}"}
        ],
        temperature=0,
        max_tokens=1,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    ).choices[0].message.content
    print(f"[is_spam] {message_content}: {openai_response}")
    return ("yes" in openai_response.lower()) or ("si" in openai_response.lower()) or ("sí" in openai_response.lower())


async def handle_message(message: Message, client: OpenAI):
    if is_spam(message.content, client):
        await message.channel.send(f"Este mensaje es posible spam. Ping a <@{MATHLIKE_USER_ID}> para que lo revise.")
        return
    if "hola" in message.content.lower():
        await message.channel.send("¡Hola!")
        return  
    if "adios" in message.content.lower():
        await message.channel.send("¡Que te vaya bien!")
        return
    if "gracias" in message.content.lower():
        await message.channel.send("¡De nada!")
        return
    if "buenos dias" in message.content.lower():
        await message.channel.send("¡Buenos días!")
        return
    if "buenas tardes" in message.content.lower():
        await message.channel.send("¡Buenas tardes!")
        return
    if "buenas noches" in message.content.lower():
        await message.channel.send("¡Buenas noches!")
        return
