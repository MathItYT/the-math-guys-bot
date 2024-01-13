from discord import Message
from openai import OpenAI
from typing import Final
import json


MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788


async def handle_message(message: Message, client: OpenAI) -> None:
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
    if BOT_USER_ID in [user.id for user in message.mentions]:
        with open("messages.json", "r") as f:
            messages: list[dict[str, str]] = json.load(f)
        messages.append({"role": "user", "content": message.content})
        response: str = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo-1106",
            temperature=0,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        ).choices[0].message.content
        print(f"[GPT-3] {message.author}: {response}")
        await message.channel.send(response)
        messages.append({"role": "assistant", "content": response})
        with open("messages.json", "w") as f:
            json.dump(messages, f)
