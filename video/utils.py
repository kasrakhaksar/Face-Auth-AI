from __future__ import annotations

from django.conf import settings
import speech_recognition as sr
import cv2
import subprocess
import os
import uuid


class SpeechRecognizer:
    def __init__(self, language: str) -> None:
        self.language: str = language

    def recognize_speech(self, audio_file_path: str) -> str:
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_file_path) as source:
            audio_data: sr.AudioData = recognizer.record(source)

        try:
            recognized_text: str = recognizer.recognize_google(
                audio_data,
                language=self.language,
            )
            return recognized_text

        except sr.UnknownValueError:
            return "I didn't understand the audio"

        except sr.RequestError:
            return "Speech recognition service is temporarily unavailable."



def extract_audio_from_video(video_file_path: str, username: str) -> str:

    audio_dir: str = os.path.join(settings.MEDIA_ROOT, username)

    os.makedirs(audio_dir, exist_ok=True)

    audio_output_path: str = os.path.join(audio_dir,f"audio_{uuid.uuid4().hex[:10]}.wav",)
    ffmpeg_command: list[str] = ["ffmpeg","-i",video_file_path,"-vn",audio_output_path,]
    subprocess.run(ffmpeg_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,)
    video_capture: cv2.VideoCapture = cv2.VideoCapture(audio_output_path)
    video_capture.release()

    return audio_output_path