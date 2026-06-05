from celery import shared_task
from django.contrib.auth.models import User
from django.db import transaction
from django.core.files.base import ContentFile
import tempfile
import os
import re
from .models import Video
from user_status.models import UserStatus
from .utils import SpeechRecognizer, extract_audio_from_video


@shared_task(bind=True, name='process_video_verification')
def process_video_verification(self, username, random_words_check, video_data, video_name):

    temp_video_path = None
    temp_audio_path = None
    
    try:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return {
                'ok': False,
                'message': f'User with username "{username}" not found',
                'status_code': 404
            }
        
        try:
            user_status = UserStatus.objects.get(user=user)
            
            if not user_status.user_idcard_status:
                return {
                    'ok': False,
                    'message': 'Please complete ID card verification first',
                    'required_step': 'id_card',
                    'status_code': 400
                }
            
            if not user_status.user_face_status:
                return {
                    'ok': False,
                    'message': 'Please complete face verification first',
                    'required_step': 'face',
                    'status_code': 400
                }
            
            if user_status.user_video_status:
                return {
                    'ok': False,
                    'message': 'This user has already completed the video verification step',
                    'already_processed': True,
                    'status_code': 400
                }
                
        except UserStatus.DoesNotExist:
            return {
                'ok': False,
                'message': 'Please complete ID card and face verification first',
                'required_steps': ['id_card', 'face'],
                'status_code': 400
            }
        
        if Video.objects.filter(user=user).exists():
            return {
                'ok': False,
                'message': 'Video already uploaded for this user',
                'already_exists': True,
                'status_code': 400
            }
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
            temp_video.write(video_data)
            temp_video_path = temp_video.name
        
        temp_audio_path = extract_audio_from_video(temp_video_path, username)
        
        if not temp_audio_path or not os.path.exists(temp_audio_path):
            return {
                'ok': False,
                'message': 'Failed to extract audio from video',
                'status_code': 400
            }
        
        speech_recognizer = SpeechRecognizer(language='fa-IR')
        recognized_text = speech_recognizer.recognize_speech(temp_audio_path)
        
        if not recognized_text:
            return {
                'ok': False,
                'message': 'No speech recognized in video',
                'status_code': 400
            }
        
        recognized_words = re.findall(r'\b\w+\b', recognized_text.lower())
        
        random_words_sorted = sorted([word.lower() for word in random_words_check])
        recognized_words_sorted = sorted([word.lower() for word in recognized_words])
        
        if random_words_sorted != recognized_words_sorted:
            missing_words = list(set(random_words_sorted) - set(recognized_words_sorted))
            extra_words = list(set(recognized_words_sorted) - set(random_words_sorted))
            
            return {
                'ok': False,
                'message': 'The spoken words do not match the expected words',
                'details': {
                    'expected_words': random_words_sorted,
                    'detected_words': recognized_words_sorted,
                    'missing_words': missing_words,
                    'extra_words': extra_words
                },
                'status_code': 400
            }
        
        with transaction.atomic():
            video_instance = Video(user=user)
            video_instance.video_field.save(video_name, ContentFile(video_data))
            video_instance.save()
            
            user_status.user_video_status = True
            user_status.save()
        
        return {
            'ok': True,
            'username': user.username,
            'message': 'Video verification completed successfully. All steps finished!',
            'status_code': 200
        }
        
    except Exception as e:
        return {
            'ok': False,
            'message': f'Video processing error: {str(e)}',
            'status_code': 400
        }
    
    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
            except:
                pass
        
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except:
                pass