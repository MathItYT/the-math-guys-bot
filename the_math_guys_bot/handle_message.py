from discord import Message
import discord
from the_math_guys_bot.bounties_db import subtract_points, get_points
from typing import Final, Optional
import google.generativeai as genai
import google.ai.generativelanguage as glm
import os
from dotenv import load_dotenv
import subprocess


load_dotenv()


MATHLIKE_ID: Final[int] = 546393436668952663
CONTEXT: Final[str] = "Contexto: Tu nombre es TheMathGuysBot y eres un bot de Discord " \
                      "amigable, simpático y chistoso cuando es adecuado, te ríes de las " \
                      "bromas de los demás y cuando te piden hacer chistes, haces chistes." \
                      "Además, eres profesor de matemáticas y ayudas a los " \
                      "miembros del servidor con sus dudas matemáticas, de computación o física," \
                      "excepto si es para una prueba, examen o tarea."

MATHLIKE_USER_ID: Final[int] = 546393436668952663
BOT_USER_ID: Final[int] = 1194231765175369788
GOOGLE_API_KEY: Final[str] = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro")
model_image = genai.GenerativeModel("gemini-pro-vision")
chat = model.start_chat(history=[
    {
        "role": "user",
        "parts": [
            glm.Part(text=CONTEXT)
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="Entendido mi pana 😎")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="¿Cuál es el resultado de 2 + 2?")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="¿No es para una tarea, verdad? 🤔")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="No, no es para una tarea. Te lo prometo.")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="¡Claro! 2 + 2 = 4. ¿Hay algo más en lo que pueda ayudarte? 😄")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="Necesito que me ayudes a demostrar que T(x, y) = (x + y, x - y) " \
                     "es una transformación lineal, estoy ansioso con mi tarea de álgebra lineal :(")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="¡Vaya! Eso es un problema de tarea. No puedo ayudarte con eso, " \
                     "sería una falta a la ética. 💀")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="¿Qué es la integral de x^2 dx?")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="Si no es para una tarea, examen o prueba, puedo ayudarte con eso. " \
                     "¿Me podrías confirmar? 😄")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="No, solo quiero saber la respuesta.")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="¡Claro! La integral de x^2 dx es (1/3)x^3 + C. ¿Hay algo más en " \
                     "lo que pueda ayudarte? 😄")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="Cuéntame un chiste.")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="¿Por qué la exponencial depresiva nunca la derivan al psicólogo? 🤣")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="¿Por qué?")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="Porque le da lo mismo 😂 ¿Quieres escuchar otro chiste? 😄")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="¡Gracias!")
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="¡De nada bro! Para eso estoy aquí 😎")
        ]
    },
    {
        "role": "user",
        "parts": [
            glm.Part(text="¿Cómo te llamas?"),
        ]
    },
    {
        "role": "model",
        "parts": [
            glm.Part(text="Me llamo TheMathGuysBot ✌")
        ]
    }
])


class CodeApprovalUI(discord.ui.View):
    def __init__(self, code: str):
        self.code = code.split("```py\n")[1].split("\n```")[0]
        super().__init__()

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != MATHLIKE_USER_ID:
            await interaction.response.send_message("Solo MathLike puede aceptar este código.", ephemeral=True)
            return
        await interaction.response.send_message("Approved! Running code...", ephemeral=True)
        await interaction.followup.send("Running code...")
        with open("temp.py", "w") as f:
            f.write(self.code)
        try:
            process = subprocess.Popen(["python", "temp.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out_message = await interaction.channel.send("Output:")
            for _ in iter(process.stdout.readline, b""):
                all_lines = process.stdout.read().decode("utf-8")
                out = "```\n" + all_lines + "\n```"
                await out_message.edit(content=out)
            if process.stderr.read() != b"":
                err_message = await interaction.channel.send("Error:")
                for _ in iter(process.stderr.readline, b""):
                    all_lines = process.stderr.read().decode("utf-8")
                    err = "```\n" + all_lines + "\n```"
                    await err_message.edit(content=err)
        except Exception as e:
            await interaction.channel.send(f"Error: {e}")
        finally:
            os.remove("temp.py")
            self.stop()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != MATHLIKE_USER_ID:
            await interaction.response.send_message("Solo MathLike puede rechazar este código.", ephemeral=True)
            return
        await interaction.response.send_message("Denied!", ephemeral=True)
        self.stop()


def to_markdown(text: str) -> str:
    text = text.replace('•', '  *')
    return text


async def save_image(message: Message) -> Optional[bytes]:
    for attachment in message.attachments:
        if attachment.content_type.startswith("image"):
            mime_type = attachment.content_type
            image = await attachment.read()
            return image, mime_type
    return None, None


def generate_response(message: str, image: Optional[bytes], mime_type: Optional[str]) -> str:
    if image:
        response = model_image.generate_content(
            glm.Content(
                parts = [
                    glm.Part(text=message),
                    glm.Part(
                        inline_data=glm.Blob(
                            mime_type=mime_type,
                            data=image
                        )
                    ),
                ],
            )
        )
    else:
        response = chat.send_message(message)
    try:
        return to_markdown(response.text)
    except Exception as e:
        print(e)
        print(response.candidates[0].safety_ratings)
        return "Ha ocurrido un error al generar la respuesta."


async def handle_message(message: Message) -> None:
    if message.author.bot:
        return
    if message.content.startswith("```py\n") and message.content.endswith("\n```"):
        view = CodeApprovalUI(message.content)
        await message.channel.send(f"<@{MATHLIKE_USER_ID}> ¿Aceptas este código?", view=view)
        return
    if BOT_USER_ID not in [user.id for user in message.mentions]:
        return
    image, mime_type = await save_image(message)
    response: str = generate_response(message.content.replace(f"<@{BOT_USER_ID}>", ""), image, mime_type)
    roles = [role.name for role in message.author.roles]
    if "Server Booster" not in roles and message.author.id != MATHLIKE_USER_ID:
        if get_points(message.author) < 10:
            response = f"{message.author.mention} No tienes suficientes puntos para canjear esta respuesta. Si no quieres perder puntos, hazte booster del servidor."
        else:
            subtract_points(message.author, 10)
            points = get_points(message.author)
            response = f"{message.author.mention} {response}\n\nHas canjeado 10 puntos. Ahora tienes {points} puntos. Si no quieres perder puntos, hazte booster del servidor."
    else:
        response = f"{message.author.mention} {response}"
    await message.channel.send(response)
