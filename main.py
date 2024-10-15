from dotenv import load_dotenv
import os
from typing import Final
from the_math_guys_bot.handle_message import handle_message, handle_welcome_message, clear_messages
from the_math_guys_bot.premium.intelligent_response import premium_handle_message
import discord
from discord.ext import commands
import json
import datetime
from pathlib import Path
from pydantic import BaseModel, Field


load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN: Final[str] = os.getenv("OPENAI_TOKEN")
GENERAL_ID: Final[int] = 1045453709221568535
SERVER_ID: Final[int] = 1045453708642758657
MATHLIKE_ID: Final[int] = 546393436668952663

bot: commands.Bot = commands.Bot(description="Soy propiedad de The Math Guys :)", intents=discord.Intents.all())


event_date = datetime.datetime.now(datetime.timezone.utc)
events_json = Path("events.json")
if not events_json.exists():
    with open(events_json, "w") as fp:
        json.dump({}, fp)
with open(events_json, "r") as fp:
    events = json.load(fp)
if "last_event" in events:
    event_date = datetime.datetime.fromisoformat(events["last_event"]) + datetime.timedelta(days=1)
limit = None
exercise = None
answer = None



@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="matemáticas"))
    print(f"Logged in as {bot.user}!")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    ctx = await bot.get_context(message)
    await premium_handle_message(message, ctx)


@bot.event
async def on_member_join(member: discord.Member):
    print(f"{member} has joined the server.")
    general = bot.get_channel(GENERAL_ID)
    await handle_welcome_message(member, general)


@bot.command(name="clear-history", help="Clears the conversation history with the bot. Only MathLike can execute this command.")
async def clear_history(ctx: commands.Context):
    if ctx.message.author.id == MATHLIKE_ID:
        clear_messages()
        ctx.send("El historial de conversación ha sido borrado.")
    else:
        ctx.send("No tienes permisos para ejecutar este comando.")


def main():
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
