from google.cloud import speech
from io import BytesIO


def speech_to_text(audio: BytesIO):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio.read())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        language_code="es-ES",
    )
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))
    return response.results[0].alternatives[0].transcript
