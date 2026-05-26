from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.contrib.auth.models import User
from django.db import transaction
import face_recognition as fr
import tempfile
import os

from .models import Face
from user_status.models import UserStatus
from id_card.models import IDCard
from .serializers import FaceSerializer
from .utils import FaceRecognizer, FaceDetector



class FaceViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        serializer = FaceSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'ok': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data.get('username')
        photo = serializer.validated_data.get('photo')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'message': f'User with username "{username}" not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user_status = UserStatus.objects.get(user=user)
            if user_status.user_face_status:
                return Response({
                    'ok': False,
                    'message': 'This user has already completed the face verification step',
                    'already_processed': True
                }, status=status.HTTP_400_BAD_REQUEST)
        except UserStatus.DoesNotExist:
            pass
        
        try:
            id_card = IDCard.objects.get(user=user)
        except IDCard.DoesNotExist:
            return Response({
                'ok': False,
                'message': 'No ID card found for this user. Please upload ID card first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        


        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(photo.name)[1]) as temp_file:
                for chunk in photo.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            face_detector = FaceDetector()
            face_detected = face_detector.crop_and_save_face(temp_path)
            
            if not face_detected:
                return Response({
                    'ok': False,
                    'message': 'No face found in the uploaded image'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            id_card_face = fr.load_image_file(id_card.photo.path)
            id_card_encodings = fr.face_encodings(id_card_face)
            
            if not id_card_encodings:
                return Response({
                    'ok': False,
                    'message': 'No face detected in the ID card image'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            encoded = {user: id_card_encodings[0]}
            face_recognizer = FaceRecognizer(encoded)
            result = face_recognizer.classify_face(temp_path)
            
            if result != user:
                return Response({
                    'ok': False,
                    'message': 'Faces do not match. The photo does not match the ID card.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                Face.objects.create(
                    user=user,
                    photo=photo 
                )
                
                user_status, created = UserStatus.objects.get_or_create(
                    user=user,
                    defaults={'user_face_status': True, 'user_idcard_status': True}
                )
                if not created:
                    user_status.user_face_status = True
                    user_status.save()
            
            return Response({
                'ok': True,
                'username': user.username,
                'message': 'Faces match successfully. Verification completed.',
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'ok': False,
                'message': f'Error processing face: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)