from dotenv import load_dotenv
import os
from typing import Final
from the_math_guys_bot.handle_message import handle_message, clear_user_and_assistant_messages
import matplotlib.pyplot as plt
import discord
import random


load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN: Final[str] = os.getenv("OPENAI_TOKEN")
GENERAL_ID: Final[int] = 1045453709221568535
SERVER_ID: Final[int] = 1045453708642758657
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


@bot.command(name="número-aleatorio", description="Genera un número aleatorio entre dos límites")
async def numero_aleatorio(ctx: discord.ApplicationContext, lower: int, upper: int):
    print(f"[Número aleatorio] {ctx.user}: {lower}, {upper}")
    await ctx.response.defer()
    number = random.randint(lower, upper)
    await ctx.followup.send(f"Número aleatorio entre {lower} y {upper}: {number}")


@bot.command(name="borrar-mensajes", description="Borra el historial")
async def borrar_mensajes(ctx: discord.ApplicationContext):
    print(f"[Borrar mensajes] {ctx.user}")
    if ctx.user.id != MATHLIKE_ID:
        await ctx.response.send_message("Solo MathLike puede usar este comando.")
        return
    await ctx.response.defer()
    clear_user_and_assistant_messages()
    await ctx.followup.send("Historial borrado.")


@bot.command(name="usuario-aleatorio", description="Muestra un usuario aleatorio del servidor")
async def usuario_aleatorio(ctx: discord.ApplicationContext):
    print(f"[Usuario aleatorio] {ctx.user}")
    await ctx.response.defer()
    members = ctx.guild.members
    random_member = members[random.randint(0, len(members) - 1)]
    random_member = random_member.name
    await ctx.followup.send(f"Usuario aleatorio: {random_member}")


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
