from dotenv import load_dotenv
import os
from typing import Final
from discord import Message, Intents, Member, Game, File, Interaction, Client, Object, Embed, RawReactionActionEvent, app_commands
from the_math_guys_bot.handle_message import handle_message
from the_math_guys_bot.plot import plot_expression
from the_math_guys_bot.bounties_db import setup_users, add_points, subtract_points, get_points, get_leaderboard, get_rank, exchange_points
import matplotlib.pyplot as plt
from the_math_guys_bot.random_problem_set import random_problem_set


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
MATHLIKE_ID: Final[int] = 546393436668952663

intents: Intents = Intents.all()
client: Client = Client(intents=intents)
tree: app_commands.CommandTree = app_commands.CommandTree(client)


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
    await handle_message(message)


@client.event
async def on_member_join(member: Member):
    print(f"{member} has joined the server.")
    general = client.get_channel(GENERAL_ID)
    await general.send(f"¡Bienvenido {member}! Acá hay muchos aficionados a las matemáticas, computación, física, etc. ¡Esperamos que te sientas como en casa! :)")
    setup_users(member.guild)


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


@tree.command(name="sumar-puntos", description="Suma puntos a un usuario", guild=Object(id=SERVER_ID))
async def sumar_puntos(interaction: Interaction, username: str, points_to_add: int):
    print(f"[Sumar puntos] {interaction.user}: {username}, {points_to_add}")
    if interaction.user.id != MATHLIKE_ID:
        await interaction.response.send_message("Solo MathLike puede usar este comando.")
        return
    await interaction.response.defer()
    add_points(username, points_to_add)
    points = get_points(username)
    await interaction.followup.send(f"Se le han sumado {points_to_add} puntos a {username}. Ahora tiene {points} puntos.")


@tree.command(name="restar-puntos", description="Resta puntos a un usuario", guild=Object(id=SERVER_ID))
async def restar_puntos(interaction: Interaction, username: str, points_to_subtract: int):
    print(f"[Restar puntos] {interaction.user}: {username}, {points_to_subtract}")
    if interaction.user.id != MATHLIKE_ID:
        await interaction.response.send_message("Solo MathLike puede usar este comando.")
        return
    await interaction.response.defer()
    subtract_points(username, points_to_subtract)
    points = get_points(username)
    await interaction.followup.send(f"Se le han restado {points_to_subtract} puntos a {username}. Ahora tiene {points} puntos.")


@tree.command(name="puntos", description="Muestra los puntos de un usuario", guild=Object(id=SERVER_ID))
async def puntos(interaction: Interaction, username: str):
    print(f"[Puntos] {interaction.user}: {username}")
    await interaction.response.defer()
    points = get_points(username)
    await interaction.followup.send(f"{username} tiene {points} puntos.")


@tree.command(name="ranking", description="Muestra el ranking de puntos", guild=Object(id=SERVER_ID))
async def ranking(interaction: Interaction):
    print(f"[Ranking] {interaction.user}")
    await interaction.response.defer()
    leaderboard = get_leaderboard()
    embed = Embed(title="Ranking de puntos")
    for i, (username, points) in enumerate(leaderboard, start=1):
        if i == 11:
            break
        embed.add_field(name=f"{i}. {username}", value=f"{points} puntos", inline=False)
    await interaction.followup.send(embed=embed)


@tree.command(name="rango", description="Muestra el rango de un usuario", guild=Object(id=SERVER_ID))
async def rango(interaction: Interaction, username: str):
    print(f"[Rango] {interaction.user}: {username}")
    await interaction.response.defer()
    rank = get_rank(username)
    await interaction.followup.send(f"{username} está en el puesto {rank}.")


@tree.command(name="intercambiar-puntos", description="Intercambia puntos entre dos usuarios", guild=Object(id=SERVER_ID))
async def intercambiar_puntos(interaction: Interaction, username1: str, username2: str, points: int):
    print(f"[Intercambiar puntos] {interaction.user}: {username1}, {username2}, {points}")
    if interaction.user.id != MATHLIKE_ID:
        await interaction.response.send_message("Solo MathLike puede usar este comando.")
        return
    await interaction.response.defer()
    exchange_points(username1, username2, points)
    points1 = get_points(username1)
    points2 = get_points(username2)
    await interaction.followup.send(f"Se han intercambiado {points} puntos entre {username1} y {username2}. Ahora {username1} tiene {points1} puntos y {username2} tiene {points2} puntos.")


@tree.command(name="graficar", description="Grafica una función", guild=Object(id=SERVER_ID))
@app_commands.describe(funciones="Las funciones a graficar separadas por ';' (sin espacios y sintaxis LaTeX)", rango_x="El rango de valores de x separados por comas (opcional)", rango_y="El rango de valores de y separados por comas (opcional)", colors="Los colores de las funciones separados por ';' y sin espacios (opcional)")
async def graficar(interaction: Interaction, funciones: str, rango_x: str = "-10,10", rango_y: str = "-10,10", colors: str = ""):
    print(f"[Graficar] {interaction.user}: {funciones}, {rango_x}, {rango_y}, {colors}")
    if not funciones:
        await interaction.response.send_message("Por favor, ingresa funciones separadas por ';' (sin espacios).")
        return
    await interaction.response.defer()
    img = plot_expression(*funciones.split(";"), x_range=tuple(map(int, rango_x.split(","))), y_range=tuple(map(int, rango_y.split(","))), colors=list(filter(lambda x: x, colors.split(";"))))
    if isinstance(img, Exception):
        await interaction.followup.send(f"Ocurrió un error al graficar la función: {img}")
        return
    await interaction.followup.send(file=File(img, "plot.png"))
    img.close()


@tree.command(name="set-aleatorio", description="Envía un set de problemas aleatorio de AMC Trivial", guild=Object(id=SERVER_ID))
async def set_aleatorio(interaction: Interaction):
    if interaction.user.id != MATHLIKE_ID:
        await interaction.response.send_message("Solo MathLike puede usar este comando.")
        return
    await interaction.response.defer()
    await interaction.followup.send(file=File(f"problems/set{random_problem_set()}.pdf"))


def main():
    plt.rcParams["figure.facecolor"] = (0, 0, 0, 0)
    plt.rcParams["axes.facecolor"] = (0, 0, 0, 0)
    plt.rcParams["savefig.facecolor"] = (0, 0, 0, 0)
    plt.rcParams["axes.edgecolor"] = (1, 1, 1, 1)
    plt.rcParams['text.color'] = (1, 1, 1, 1)
    plt.rcParams['axes.labelcolor'] = (1, 1, 1, 1)
    plt.rcParams['xtick.color'] = (1, 1, 1, 1)
    plt.rcParams['ytick.color'] = (1, 1, 1, 1)
    plt.rcParams["figure.figsize"] = (2000/300, 2000/300)
    plt.rcParams["figure.dpi"] = 300
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
