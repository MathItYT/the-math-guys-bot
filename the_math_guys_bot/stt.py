from google.cloud import speech


def speech_to_text(audio: bytes):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        language_code="es-ES",
    )
    response = client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript
