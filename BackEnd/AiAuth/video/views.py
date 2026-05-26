from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.contrib.auth.models import User
from django.db import transaction
import tempfile
import os
import re

from .models import Video
from user_status.models import UserStatus
from .serializers import VideoSerializer
from .utils import SpeechRecognizer, extract_audio_from_video


class VideoViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        serializer = VideoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'ok': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        username = validated_data.get('username')
        random_words_check = validated_data.get('randomCheck')
        video_file = validated_data.get('video')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'message': f'User with username "{username}" not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user_status = UserStatus.objects.get(user=user)
            
            if not user_status.user_idcard_status:
                return Response({
                    'ok': False,
                    'message': 'Please complete ID card verification first',
                    'required_step': 'id_card'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not user_status.user_face_status:
                return Response({
                    'ok': False,
                    'message': 'Please complete face verification first',
                    'required_step': 'face'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if user_status.user_video_status:
                return Response({
                    'ok': False,
                    'message': 'This user has already completed the video verification step',
                    'already_processed': True
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except UserStatus.DoesNotExist:
            return Response({
                'ok': False,
                'message': 'Please complete ID card and face verification first',
                'required_steps': ['id_card', 'face']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if Video.objects.filter(user=user).exists():
            return Response({
                'ok': False,
                'message': 'Video already uploaded for this user',
                'already_exists': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        temp_video_path = None
        temp_audio_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                for chunk in video_file.chunks():
                    temp_video.write(chunk)
                temp_video_path = temp_video.name
            
            temp_audio_path = extract_audio_from_video(temp_video_path, f"temp_{username}")
            
            if not temp_audio_path or not os.path.exists(temp_audio_path):
                return Response({
                    'ok': False,
                    'message': 'Failed to extract audio from video'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            speech_recognizer = SpeechRecognizer(language='en')
            recognized_text = speech_recognizer.recognize_speech(temp_audio_path)
            
            if not recognized_text:
                return Response({
                    'ok': False,
                    'message': 'No speech recognized in video'
                }, status=status.HTTP_400_BAD_REQUEST)
            
   
            recognized_words = re.findall(r'\b\w+\b', recognized_text.lower())
            # recognized_words = re.findall(r'[\u0600-\u06FF0-9]+', recognized_text)
 
            random_words_sorted = sorted([word.lower() for word in random_words_check])
            recognized_words_sorted = sorted([word.lower() for word in recognized_words])
            
            if random_words_sorted != recognized_words_sorted:
                missing_words = list(set(random_words_sorted) - set(recognized_words_sorted))
                extra_words = list(set(recognized_words_sorted) - set(random_words_sorted))
                
                if temp_audio_path and os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                
                return Response({
                    'ok': False,
                    'message': 'The spoken words do not match the expected words',
                    'details': {
                        'expected_words': random_words_sorted,
                        'detected_words': recognized_words_sorted,
                        'missing_words': missing_words,
                        'extra_words': extra_words
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                Video.objects.create(
                    user=user,
                    video_field=video_file
                )
                
                user_status.user_video_status = True
                user_status.save()
            
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            
            return Response({
                'ok': True,
                'username': user.username,
                'message': 'Video verification completed successfully. All steps finished!',
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'ok': False,
                'message': f'Video processing error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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