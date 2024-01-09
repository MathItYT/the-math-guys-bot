from dotenv import load_dotenv
import os
from typing import Final
from openai import OpenAI
from discord import Message, Intents, Member, Game, Interaction, Client, Object, app_commands
from the_math_guys_bot.handle_message import handle_message
from datetime import datetime


load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN: Final[str] = os.getenv("OPENAI_TOKEN")
GENERAL_ID: Final[int] = 1045453709221568535
SERVER_ID: Final[int] = 1045453708642758657
MAX_GPT_QUESTIONS_PER_DAY: Final[int] = 5
current_questions: int = 0

intents: Intents = Intents.all()
client: Client = Client(intents=intents)
tree: app_commands.CommandTree = app_commands.CommandTree(client)
current_day: int = datetime.now().day

openai_client: OpenAI = OpenAI(api_key=OPENAI_TOKEN)
messages: list[dict[str, str]] = [
    {"role": "system", "content": "Eres un asistente que habla español y debe responder "
     "preguntas sobre temas de matemáticas, física, computación, o cualquier otra ciencia. "
     "Debes dejar una respuesta justificada, pero no siempre completa. "
     "Debes dejar interrogantes para que el usuario cuestione por sí mismo."}
]


@client.event
async def on_ready():
    await tree.sync(guild=Object(id=SERVER_ID))
    await client.change_presence(activity=Game(name="matemáticas"))
    print(f"Logged in as {client.user}!")


@client.event
async def on_message(message: Message):
    if message.author == client.user:
        return
    
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await handle_message(message, openai_client)


@client.event
async def on_member_join(member: Member):
    print(f"{member} has joined the server.")
    general = client.get_channel(GENERAL_ID)
    await general.send(f"¡Bienvenido {member}! Acá hay muchos aficionados a las matemáticas, computación, física, etc. ¡Esperamos que te sientas como en casa! :)")


@tree.command(name="gpt", description="Haz una pregunta a GPT-3", guild=Object(id=SERVER_ID))
@app_commands.describe(question="La pregunta que quieres hacerle a GPT-3")
async def gpt(interaction: Interaction, question: str):
    global current_questions, current_day, messages
    if current_day == datetime.now().day and current_questions >= MAX_GPT_QUESTIONS_PER_DAY:
        await interaction.response.send_message(f"Ya se han hecho {MAX_GPT_QUESTIONS_PER_DAY} preguntas hoy. Por favor, intenta de nuevo mañana :)")
        return
    if current_day != datetime.now().day:
        current_day = datetime.now().day
        current_questions = 0
        messages = messages[:1]
    if not question:
        await interaction.response.send_message("Por favor, haz una pregunta.")
        return
    print(f"[GPT-3] {interaction.user}: {question}")
    messages.append({"role": "user", "content": question})
    await interaction.response.defer()
    answer: str = openai_client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo-1106",
        temperature=0,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    ).choices[0].message.content
    print(f"[GPT-3] {interaction.user}: {answer}")
    await interaction.response.edit_message(f"""Pregunta: {question}

Respuesta: {answer}

Quedan {MAX_GPT_QUESTIONS_PER_DAY - current_questions - 1} preguntas hoy.""")
    current_questions += 1


def main():
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
