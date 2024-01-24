from google.cloud import speech
from google.cloud import storage
from io import BytesIO


def speech_to_text(audio: BytesIO):
    client = speech.SpeechClient()
    bucket_name = "the-math-guys"
    bucket = storage.Client().bucket(bucket_name)
    blob = bucket.blob("audio.wav")
    blob.upload_from_file(audio)
    uri = f"gs://{bucket_name}/audio.wav"
    audio = speech.RecognitionAudio(uri=uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="es"
    )
    response = client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript
