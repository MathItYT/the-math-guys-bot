from dotenv import load_dotenv
import os
from typing import Final
from openai import OpenAI
from discord import Message, Intents, Member, Game, Interaction, Client, Object, Guild, Embed, RawReactionActionEvent, app_commands
from discord import utils
from the_math_guys_bot.handle_message import handle_message
from datetime import datetime


load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN: Final[str] = os.getenv("OPENAI_TOKEN")
GENERAL_ID: Final[int] = 1045453709221568535
SERVER_ID: Final[int] = 1045453708642758657
MAX_GPT_QUESTIONS_PER_DAY: Final[int] = 5
current_questions: int = 0
EMOJI_MAP: Final[dict[int, str]] = {
    1: ":one:",
    2: ":two:",
    3: ":three:",
    4: ":four:",
    5: ":five:",
    6: ":six:",
    7: ":seven:",
    8: ":eight:",
    9: ":nine:"
}

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
    await interaction.response.defer()
    messages.append({"role": "user", "content": question})
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
    await interaction.followup.send(f"""Pregunta: {question}

Respuesta: {answer}

Quedan {MAX_GPT_QUESTIONS_PER_DAY - current_questions - 1} preguntas hoy.""")
    current_questions += 1
    messages.append({"role": "assistant", "content": answer})


@tree.command(name="crear-encuesta", description="Crea una encuesta", guild=Object(id=SERVER_ID))
@app_commands.describe(pregunta="La pregunta que los usuarios deberán responder", opciones="Las opciones de la encuesta separadas por comas (máximo 9)")
async def crear_encuesta(interaction: Interaction, pregunta: str, opciones: str):
    print(f"[Encuesta] {interaction.user}: {pregunta}, {opciones}")
    if not opciones or not pregunta:
        await interaction.response.send_message("Por favor, ingresa las opciones separadas por comas.")
        return
    await interaction.response.defer()
    opciones = opciones.split(",")
    if len(opciones) > 9:
        await interaction.followup.send("No puedes tener más de 9 opciones.")
        return
    opciones_emoji: str = ""
    for i, opcion in enumerate(opciones, start=1):
        opciones_emoji += f"{EMOJI_MAP[i]}: {opcion}\n"
    embed = Embed(title=pregunta,
                  description=f"Reacciona con el emoji correspondiente a la opción que quieras elegir.\n\n{opciones_emoji}")
    embed.set_footer(text=f"Encuesta creada por {interaction.user}")
    message: Message = await interaction.followup.send(embed=embed, wait=True)
    for i in range(1, len(opciones) + 1):
        await message.add_reaction(utils.get(interaction.guild.emojis, name=EMOJI_MAP[i][1:-1]))
    with open("polls_ids.txt", "a") as f:
        f.write(f"{message.id}\n")


@client.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    message_id: int = payload.message_id
    if message_id not in [int(line) for line in open("polls_ids.txt", "r").readlines()]:
        return
    message: Message = await client.get_channel(payload.channel_id).fetch_message(message_id)
    if not message.embeds:
        return
    embed: Embed = message.embeds[0]
    options_number: int = len(embed.description.split("\n\n")[1].split("\n"))
    if payload.emoji in [utils.get(message.guild.emojis, name=EMOJI_MAP[i][1:-1]).name for i in range(1, options_number + 1)]:
        return
    await message.remove_reaction(payload.emoji, payload.member)
    await payload.member.send("Por favor, reacciona con un emoji válido.")


def main():
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
