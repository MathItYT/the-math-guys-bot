from dotenv import load_dotenv
import os
from typing import Final
from the_math_guys_bot.handle_message import handle_message, new_video_message
from the_math_guys_bot.retrieve_youtube import retrieve_new_youtube_videos 
import discord
from discord.ext import tasks
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


@bot.command(name="usuario-aleatorio", description="Muestra un usuario aleatorio del servidor")
async def usuario_aleatorio(ctx: discord.ApplicationContext):
    print(f"[Usuario aleatorio] {ctx.user}")
    await ctx.response.defer()
    members = ctx.guild.members
    random_member = members[random.randint(0, len(members) - 1)]
    random_member = random_member.name
    await ctx.followup.send(f"Usuario aleatorio: {random_member}")


@tasks.loop(seconds=60)
async def update_youtube_videos():
    print("Updating YouTube latest videos...")
    new_videos = retrieve_new_youtube_videos("channels.json")
    if len(new_videos) == 0:
        print("No new videos found.")
        return
    general = bot.get_channel(GENERAL_ID)
    for new_video in new_videos:
        print(f"New video: {new_video}")
        response = new_video_message(new_video)
        await general.send(response)


def main():
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
