from dotenv import load_dotenv
import os
from typing import Final
from the_math_guys_bot.handle_message import handle_message, handle_welcome_message, clear_messages
from the_math_guys_bot.premium.intelligent_response import premium_handle_message
import discord
from discord.ext import commands, tasks
import json
import datetime
from absl import app
from pathlib import Path
from mathematics_dataset.mathematics_dataset import generate
import random
from the_math_guys_bot import message_history
from pydantic import BaseModel, Field


load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
OPENAI_TOKEN: Final[str] = os.getenv("OPENAI_TOKEN")
GENERAL_ID: Final[int] = 1045453709221568535
SERVER_ID: Final[int] = 1045453708642758657
MATHLIKE_ID: Final[int] = 546393436668952663

bot: commands.Bot = commands.Bot(description="Soy propiedad de The Math Guys :)", intents=discord.Intents.all())


class AnswerClassifier(BaseModel):
    answer_classify: bool | None = Field(description="Si es la respuesta correcta, es True. Si es incorrecta, False. Si no corresponde a una respuesta, es None.")


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
    activity.start()
    print(f"Logged in as {bot.user}!")


async def handle_answer(message: discord.Message):
    global limit, answer, exercise, event_date, events
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)
    print(f'[{channel}] {username}: "{user_message}"')
    if message.author.id == MATHLIKE_ID:
        return
    client = message_history.client
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": f"La respuesta correcta es {answer}. Debes clasificar la respuesta del usuario. Si es correcta, answer_classify es True. Si es incorrecta, answer_classify es False. Si no corresponde a una respuesta, answer_classify es None."
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        response_format=AnswerClassifier
    )
    answer_classification = response.choices[0].message.parsed.answer_classify
    if answer_classification is None:
        return
    if answer_classification:
        general = bot.get_channel(GENERAL_ID)
        await general.send(f"{message.author.mention} ha respondido correctamente al evento de hoy. ¡Felicidades!", reference=message)
        check_time.stop()
        limit = None
        answer = None
        exercise = None
        event_date = event_date + datetime.timedelta(days=1)
        if "winners" not in events:
            events["winners"] = {}
        events["winners"][str(message.author.id)] = events["winners"].get(str(message.author.id), 0) + 0.5
        with open(events_json, "w") as fp:
            json.dump(events, fp)
    else:
        general = bot.get_channel(GENERAL_ID)
        await general.send(f"{message.author.mention} Respuesta incorrecta, ¡sigue intentando!", reference=message)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)
    if limit is not None and datetime.datetime.now(datetime.timezone.utc) < limit:
        await handle_answer(message)
        return
    with open("premium.json", "r") as fp:
        premium_users = json.load(fp)
    if message.author.id in premium_users:
        print(f'[{channel}] {username} (PREMIUM): "{user_message}"')
        ctx = await bot.get_context(message)
        await premium_handle_message(message, ctx)
        return
    print(f'[{channel}] {username}: "{user_message}"')
    await handle_message(message)


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


def generate_question_and_answer() -> None:
    global exercise, answer
    generate.init_modules(True)
    modules = generate.filtered_modules["train-easy"]
    modules = random.choice(list(modules.values()))
    problem, _ = generate.sample_from_module(modules)
    exercise = problem.question
    answer = problem.answer


@tasks.loop(seconds=30)
async def activity() -> None:
    global event_date, limit, answer, exercise
    now = datetime.datetime.now(datetime.timezone.utc)
    print(event_date)
    if limit is not None:
        return
    if now < event_date:
        return
    with open(events_json, "w") as fp:
        json.dump({"last_event": event_date.isoformat()}, fp)
    generate_question_and_answer()
    general = bot.get_channel(GENERAL_ID)
    limit = event_date + datetime.timedelta(minutes=10)
    discord_timestamp = int(limit.timestamp())
    event_date = event_date + datetime.timedelta(days=1)
    print(f"[ANSWER] {answer}")
    await general.send(f"@everyone Tienen hasta las <t:{discord_timestamp}:T> para enviar sus respuestas al evento de hoy. Acumularán $0.5 dólares para ganar a fin de mes. ¡Solo respuestas hasta que se termine el tiempo o alguien responda! ¡Buena suerte!\n\n**Ejercicio:**\n```\n{exercise}```", allowed_mentions=discord.AllowedMentions(everyone=True))
    check_time.start()


@tasks.loop(minutes=2)
async def check_time() -> None:
    global limit, answer, event_date, exercise
    now = datetime.datetime.now(datetime.timezone.utc)
    print(f"[TIME] {now} [LIMIT] {limit}")
    if now >= limit:
        general = bot.get_channel(GENERAL_ID)
        await general.send("@everyone Se ha acabado el tiempo para enviar sus respuestas al evento de hoy.")
        limit = None
        answer = None
        exercise = None
        event_date = event_date + datetime.timedelta(days=1)
        check_time.stop()


def main():
    app.run(lambda argv: bot.run(DISCORD_TOKEN))


if __name__ == "__main__":
    main()
