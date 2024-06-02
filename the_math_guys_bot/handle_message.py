from discord import Message
import discord
from the_math_guys_bot.bounties_db import subtract_points, get_points
from typing import Final, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
import subprocess
import shutil
import re
import base64


load_dotenv()


MATHLIKE_ID: Final[int] = 546393436668952663
CONTEXT: Final[str] = "Contexto: Tu nombre es TheMathGuysBot y eres un bot de Discord " \
                      "amigable, simpático y chistoso cuando es adecuado, te ríes de las " \
                      "bromas de los demás y cuando te piden hacer chistes, haces chistes. " \
                      "Además, eres profesor de matemáticas y ayudas a los " \
                      "miembros del servidor con sus dudas matemáticas, de computación o física, " \
                      "activando su pensamiento crítico y resolviendo de forma interactiva " \
                      "los problemas que te plantean."

MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
OPENAI_API_KEY: Final[str] = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=OPENAI_API_KEY
)
messages: list[dict[str, str]] = [
    {"role": "system", "content": CONTEXT}
]

# It must include scene name and scene arguments if any
MANIM_REGEX = re.compile(r"# manim: (?P<scene_name>\w+)( (?P<scene_args>.*))?")

def stream_process(process: subprocess.Popen) -> tuple[str, int | None]:
    go = process.poll()
    lines = []
    for line in process.stdout:
        lines.append(line.decode("utf-8"))
    return "".join(lines), go


def get_media_recursive(directory: str) -> list[str]:
    result = []
    for root, _, files in os.walk(directory):
        for f in files:
            f_now = os.path.join(root, f)
            if os.path.isdir(f_now):
                result += get_media_recursive(f_now)
                continue
            if f_now.endswith(".mp4") or f_now.endswith(".png") or f_now.endswith(".jpg") or f_now.endswith(".jpeg") or f_now.endswith(".gif"):
                result.append(f_now)
    return result


class CodeApprovalUI(discord.ui.View):
    def __init__(self, code: str):
        self.code = code.removeprefix("```py\n").removesuffix("\n```")
        super().__init__()

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != MATHLIKE_USER_ID:
            await interaction.response.send_message("Solo MathLike puede aceptar este código.", ephemeral=True)
            return
        await interaction.channel.send("Approved! The code will be executed.")
        await interaction.message.delete()
        first_line = self.code.split("\n")[0]
        match = MANIM_REGEX.match(first_line)
        if not match:
            await self.run_code(interaction)
            return
        await self.run_manim(interaction, match.group("scene_name"), match.group("scene_args"))
    
    async def run_manim(self, interaction: discord.Interaction, scene_name: str, scene_args: str):
        with open("manim_temp.py", "w") as f:
            f.write(self.code)
        try:
            scene_args = scene_args.split(" ")
            if "-p" in scene_args or "--preview" in scene_args:
                while "-p" in scene_args:
                    scene_args.remove("-p")
                while "--preview" in scene_args:
                    scene_args.remove("--preview")
            process = subprocess.Popen(["manim", "manim_temp.py", scene_name, *scene_args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out_message = await interaction.channel.send("Output:")
            while True:
                out, go = stream_process(process)
                if len(out) > 1000:
                    message = "The output is too long."
                    await out_message.edit(content=message)
                else:
                    await out_message.edit(content="Output:\n```\n" + out + "\n```")
                if go is not None:
                    break
            err = process.stderr.read().decode("utf-8")
            if err and len(err) < 1000:
                await interaction.channel.send("Error:\n```\n" + err + "\n```")
            elif err:
                await interaction.channel.send("Error: Error not shown because it is too long.")
        except Exception as e:
            await interaction.channel.send(f"Error: {e}")
        finally:
            os.remove("manim_temp.py")
            media_videos = "media/videos"
            media_images = "media/images"
            files = get_media_recursive(media_videos) + get_media_recursive(media_images)
            for f in files:
                if f.split("/")[-1].split(".")[0] != scene_name and f.split("/")[-1].split(".")[0] != f"{scene_name}_ManimCE_v0":
                    continue
                with open(f, "rb") as f_:
                    await interaction.channel.send(file=discord.File(f_, f.split("/")[-1]))
            shutil.rmtree(media_videos)
            shutil.rmtree(media_images)
            self.stop()

    async def run_code(self, interaction: discord.Interaction):
        try:
            process = subprocess.Popen(["python", "-c", self.code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out_message = await interaction.channel.send("Output:")
            while True:
                out, go = stream_process(process)
                if len(out) > 1000:
                    message = "The output is too long."
                    await out_message.edit(content=message)
                else:
                    await out_message.edit(content="Output:\n```\n" + out + "\n```")
                if go is not None:
                    break
            err = process.stderr.read().decode("utf-8")
            if err and len(err) < 1000:
                await interaction.channel.send("Error:\n```\n" + err + "\n```")
            elif err:
                await interaction.channel.send("Error: Error not shown because it is too long.")
        except Exception as e:
            await interaction.channel.send(f"Error: {e}")
        finally:
            self.stop()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != MATHLIKE_USER_ID:
            await interaction.response.send_message("Solo MathLike puede rechazar este código.", ephemeral=True)
            return
        await interaction.channel.send("Denied! The code will not be executed.")
        await interaction.message.delete()
        self.stop()


async def get_images(message: Message) -> list[dict[str, str]]:
    images = []
    for attachment in message.attachments:
        if attachment.content_type.startswith("image/"):
            base64_image = base64.b64encode(await attachment.read()).decode("utf-8")
            images.append({
                "type": "image_url",
                "url": f"data:{attachment.content_type};base64,{base64_image}"
            })
    return images
        


def generate_response(message: str, images: list[dict[str, str]]) -> str:
    global messages
    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": message}
        ] + images
    })
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=500
    )
    content = response.choices[0].message.content
    messages.append({
        "role": "assistant",
        "content": content
    })
    return content


async def handle_message(message: Message) -> None:
    if message.author.bot:
        return
    if message.content.startswith("```py\n") and message.content.endswith("\n```"):
        view = CodeApprovalUI(message.content)
        await message.channel.send(f"<@{MATHLIKE_USER_ID}> ¿Aceptas este código?", view=view)
        return
    if BOT_USER_ID not in [user.id for user in message.mentions]:
        return
    images = await get_images(message)
    response = generate_response(message.content, images)
    await message.channel.send(response)
