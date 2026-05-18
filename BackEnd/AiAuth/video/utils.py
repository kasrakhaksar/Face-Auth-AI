from django.conf import settings
import speech_recognition as sr
import cv2
import subprocess
import os


class SpeechRecognizer:

    def __init__(self, language):
        self.language = language

    def recognize_speech(self, audio_file_path):

        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)

        try:
            recognized_text = recognizer.recognize_google(audio_data, language=self.language)
            return recognized_text
        except sr.UnknownValueError:
            return "I didn't understand the audio"
        except sr.RequestError:
            return "Speech recognition service is temporarily unavailable."



def extract_audio_from_video(video_file_path, username):
    audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
    
    os.makedirs(audio_dir, exist_ok=True)
    
    audio_output_path = os.path.join(audio_dir, f'{username}_audio.wav')
    
    ffmpeg_command = ['ffmpeg', '-i', video_file_path, '-vn', audio_output_path]
    subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    video_capture = cv2.VideoCapture(audio_output_path)
    video_capture.release()
    
    return audio_output_path