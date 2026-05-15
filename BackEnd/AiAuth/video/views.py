from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from user_status.models import UserStatus
from .serializers import VideoSerializer
from .models import Video
from django.contrib.auth.models import User
import os
import re
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
        
        if not random_words_check or len(random_words_check) == 0:
            return Response({
                'ok': False,
                'message': 'Random words list cannot be empty'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        video_user = None
        
        try:
            video_user = serializer.save()
            video_path = video_user.video.path
            
            audio_path = extract_audio_from_video(video_path, username)
            
            if not audio_path or not os.path.exists(audio_path):
                video_user.delete()
                return Response({
                    'ok': False,
                    'message': 'Failed to extract audio from video'
                }, status=status.HTTP_400_BAD_REQUEST)
            


            speechrecognizer = SpeechRecognizer(language='en')
            recognized_text = speechrecognizer.recognize_speech(audio_path)
            
            try:
                os.remove(audio_path)
            except:
                pass
            
            if not recognized_text:
                video_user.delete()
                return Response({
                    'ok': False,
                    'message': 'No speech recognized in video'
                }, status=status.HTTP_400_BAD_REQUEST)
            


            recognized_text_words = re.findall(r'[\u0600-\u06FF0-9]+', recognized_text)
            
            random_words_check_sorted = sorted([word.strip().lower() for word in random_words_check])
            recognized_text_words_sorted = sorted([word.strip().lower() for word in recognized_text_words])
            
            if random_words_check_sorted == recognized_text_words_sorted:
                user_status.user_video_status = True
                user_status.save()
                
                return Response({
                    'ok': True,
                    'username': user.username,
                    'message': 'Video verification completed successfully. All steps finished!',
                    'details': {
                        'expected_words': random_words_check_sorted,
                        'detected_words': recognized_text_words_sorted
                    }
                }, status=status.HTTP_200_OK)
            else:
                video_user.delete()
                
                missing_words = list(set(random_words_check_sorted) - set(recognized_text_words_sorted))
                extra_words = list(set(recognized_text_words_sorted) - set(random_words_check_sorted))
                
                return Response({
                    'ok': False,
                    'message': 'The spoken words do not match the expected words',
                    'details': {
                        'expected_words': random_words_check_sorted,
                        'detected_words': recognized_text_words_sorted,
                        'missing_words': missing_words,
                        'extra_words': extra_words
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            if video_user:
                try:
                    video_user.delete()
                except:
                    pass
            
            return Response({
                'ok': False,
                'message': f'Video processing error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)