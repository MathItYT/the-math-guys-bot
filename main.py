from dotenv import load_dotenv
import os
from typing import Final
from openai import OpenAI
from discord import Message, Intents, Member, Game, File, Interaction, Client, Object, Embed, RawReactionActionEvent, app_commands
from the_math_guys_bot.handle_message import handle_message
from the_math_guys_bot.plot import plot_expression
import json
import matplotlib.pyplot as plt


load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN: Final[str] = os.getenv("OPENAI_TOKEN")
GENERAL_ID: Final[int] = 1045453709221568535
SERVER_ID: Final[int] = 1045453708642758657
EMOJI_MAP: Final[dict[int, str]] = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣"
}
SYSTEM_MESSAGE: Final[str] = f"""Eres un bot en español que tiene dos formas de comportarse.
La primera es como un bot amistoso e informal, que bromea y responde a mensajes de forma casual.
La segunda es como profesor, donde deberás responder preguntas académicas de forma clara y concisa."""

intents: Intents = Intents.all()
client: Client = Client(intents=intents)
tree: app_commands.CommandTree = app_commands.CommandTree(client)

openai_client: OpenAI = OpenAI(api_key=OPENAI_TOKEN)
with open("messages.json", "w") as f:
    json.dump(
        [
            {"role": "system", "content": SYSTEM_MESSAGE}
        ], f
    )


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
    with open("messages.json", "r") as f:
        messages: list[dict[str, str]] = json.load(f)
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

Respuesta: {answer}""")
    current_questions += 1
    messages.append({"role": "assistant", "content": answer})
    with open("messages.json", "w") as f:
        json.dump(messages, f)


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
        await message.add_reaction(EMOJI_MAP[i])
    with open("polls_ids.txt", "a") as f:
        f.write(f"{message.id}\n")


@client.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    if payload.member.bot:
        return
    message_id: int = payload.message_id
    if message_id not in [int(line) for line in open("polls_ids.txt", "r").readlines()]:
        return
    message: Message = await client.get_channel(payload.channel_id).fetch_message(message_id)
    if not message.embeds:
        return

    member_reactions: int = 0
    
    for reaction in message.reactions:
        async for user in reaction.users():
            if user.id == payload.user_id:
                member_reactions += 1
    if member_reactions > 1:
        await message.remove_reaction(payload.emoji, payload.member)
        await payload.member.send("Solo puedes reaccionar una vez por encuesta.")
        return
    
    embed: Embed = message.embeds[0]
    options_number: int = len(embed.description.split("\n\n")[1].split("\n"))
    if payload.emoji.name in list(EMOJI_MAP.values())[:options_number]:
        return
    await message.remove_reaction(payload.emoji, payload.member)
    await payload.member.send("Por favor, reacciona con un emoji válido.")


@tree.command(name="graficar", description="Grafica una función", guild=Object(id=SERVER_ID))
@app_commands.describe(funciones="Las funciones a graficar separadas por ';' (sin espacios)", rango_x="El rango de valores de x separados por comas (opcional)", rango_y="El rango de valores de y separados por comas (opcional)", colors="Los colores de las funciones separados por ';' y sin espacios (opcional)")
async def graficar(interaction: Interaction, funciones: str, rango_x: str = "-10,10", rango_y: str = "-10,10", colors: str = ""):
    print(f"[Graficar] {interaction.user}: {funciones}, {rango_x}, {rango_y}, {colors}")
    if not funciones:
        await interaction.response.send_message("Por favor, ingresa funciones separadas por ';' (sin espacios).")
        return
    await interaction.response.defer()
    img = plot_expression(*funciones.split(";"), tuple(map(int, rango_x.split(","))), tuple(map(int, rango_y.split(","))), colors.split(";"))
    if isinstance(img, Exception):
        await interaction.followup.send(f"Ocurrió un error al graficar la función: {img}")
        return
    await interaction.followup.send(file=File(img, "plot.png"))
    img.close()


def main():
    plt.rcParams['text.usetex'] = True
    plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
