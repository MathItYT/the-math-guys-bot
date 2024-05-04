from dotenv import load_dotenv
import os
from typing import Final
from the_math_guys_bot.handle_message import handle_message
from the_math_guys_bot.plot import plot_expression
from the_math_guys_bot.bounties_db import setup_users, add_points, subtract_points, get_points, get_leaderboard, get_rank, exchange_points
import matplotlib.pyplot as plt
from the_math_guys_bot.random_problem_set import random_problem_set
import discord


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

bot: discord.Bot = discord.Bot(description="Soy propiedad de The Math Guys :)", intents=discord.Intents.all())
connections = {}


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="matemáticas"))
    print(f"Logged in as {bot.user}!")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await handle_message(message)


@bot.event
async def on_member_join(member: discord.Member):
    print(f"{member} has joined the server.")
    general = bot.get_channel(GENERAL_ID)
    await general.send(f"¡Bienvenido {member}! Acá hay muchos aficionados a las matemáticas, computación, física, etc. ¡Esperamos que te sientas como en casa! :)")
    setup_users(member.guild)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.member.bot:
        return
    message_id: int = payload.message_id
    if message_id not in [int(line) for line in open("polls_ids.txt", "r").readlines()]:
        return
    message: discord.Message = await bot.get_channel(payload.channel_id).fetch_message(message_id)
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
    
    embed: discord.Embed = message.embeds[0]
    options_number: int = len(embed.description.split("\n\n")[1].split("\n"))
    if payload.emoji.name in list(EMOJI_MAP.values())[:options_number]:
        return
    await message.remove_reaction(payload.emoji, payload.member)
    await payload.member.send("Por favor, reacciona con un emoji válido.")


@bot.command(name="sumar-puntos", description="Suma puntos a un usuario")
async def sumar_puntos(ctx: discord.ApplicationContext, username: str, points_to_add: int):
    print(f"[Sumar puntos] {ctx.user}: {username}, {points_to_add}")
    if ctx.user.id != MATHLIKE_ID:
        await ctx.response.send_message("Solo MathLike puede usar este comando.")
        return
    await ctx.response.defer()
    user = ctx.guild.get_member_named(username)
    add_points(user, points_to_add)
    points = get_points(username)
    await ctx.followup.send(f"Se le han sumado {points_to_add} puntos a {username}. Ahora tiene {points} puntos.")


@bot.command(name="restar-puntos", description="Resta puntos a un usuario")
async def restar_puntos(ctx: discord.ApplicationContext, username: str, points_to_subtract: int):
    print(f"[Restar puntos] {ctx.user}: {username}, {points_to_subtract}")
    if ctx.user.id != MATHLIKE_ID:
        await ctx.response.send_message("Solo MathLike puede usar este comando.")
        return
    await ctx.response.defer()
    user = ctx.guild.get_member_named(username)
    subtract_points(user, points_to_subtract)
    points = get_points(username)
    await ctx.followup.send(f"Se le han restado {points_to_subtract} puntos a {username}. Ahora tiene {points} puntos.")


@bot.command(name="puntos", description="Muestra los puntos de un usuario")
async def puntos(ctx: discord.ApplicationContext, username: str):
    print(f"[Puntos] {ctx.user}: {username}")
    await ctx.response.defer()
    user = ctx.guild.get_member_named(username)
    points = get_points(user)
    await ctx.followup.send(f"{username} tiene {points} puntos.")


@bot.command(name="ranking", description="Muestra el ranking de puntos")
async def ranking(ctx: discord.ApplicationContext):
    print(f"[Ranking] {ctx.user}")
    await ctx.response.defer()
    leaderboard = await get_leaderboard(ctx.guild)
    embed = discord.Embed(title="Ranking de puntos")
    for i, (username, points) in enumerate(leaderboard, start=1):
        embed.add_field(name=f"{i}. {username}", value=f"{points} puntos", inline=False)
    await ctx.followup.send(embed=embed)


@bot.command(name="rango", description="Muestra el rango de un usuario")
async def rango(ctx: discord.ApplicationContext, username: str):
    print(f"[Rango] {ctx.user}: {username}")
    await ctx.response.defer()
    user = ctx.guild.get_member_named(username)
    rank = get_rank(user.id)
    await ctx.followup.send(f"{username} está en el puesto {rank}.")


@bot.command(name="intercambiar-puntos", description="Intercambia puntos entre dos usuarios")
async def intercambiar_puntos(ctx: discord.ApplicationContext, username1: str, username2: str, points: int):
    print(f"[Intercambiar puntos] {ctx.user}: {username1}, {username2}, {points}")
    if ctx.user.id != MATHLIKE_ID:
        await ctx.response.send_message("Solo MathLike puede usar este comando.")
        return
    await ctx.response.defer()
    user1 = ctx.guild.get_member_named(username1)
    user2 = ctx.guild.get_member_named(username2)
    exchange_points(user1, user2, points)
    points1 = get_points(username1)
    points2 = get_points(username2)
    await ctx.followup.send(f"Se han intercambiado {points} puntos entre {username1} y {username2}. Ahora {username1} tiene {points1} puntos y {username2} tiene {points2} puntos.")


@bot.command(name="graficar", description="Grafica una función")
async def graficar(ctx: discord.ApplicationContext, funciones: str, rango_x: str = "-10,10", rango_y: str = "-10,10", colors: str = ""):
    print(f"[Graficar] {ctx.user}: {funciones}, {rango_x}, {rango_y}, {colors}")
    if not funciones:
        await ctx.response.send_message("Por favor, ingresa funciones separadas por ';' (sin espacios).")
        return
    await ctx.response.defer()
    img = plot_expression(*funciones.split(";"), x_range=tuple(map(int, rango_x.split(","))), y_range=tuple(map(int, rango_y.split(","))), colors=list(filter(lambda x: x, colors.split(";"))))
    if isinstance(img, Exception):
        await ctx.followup.send(f"Ocurrió un error al graficar la función: {img}")
        return
    await ctx.followup.send(content=f"Funciones graficadas: {",".join(funciones.split(';'))}", file=discord.File(img, "plot.png"))
    img.close()


@bot.command(name="set-aleatorio", description="Envía un set de problemas aleatorio de AMC Trivial")
async def set_aleatorio(ctx: discord.ApplicationContext):
    if ctx.user.id != MATHLIKE_ID:
        await ctx.response.send_message("Solo MathLike puede usar este comando.")
        return
    await ctx.response.defer()
    await ctx.followup.send(file=discord.File(f"problems/set{random_problem_set()}.pdf"))


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
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
