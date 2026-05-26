from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.db import transaction
import tempfile
import os

from .models import IDCard
from user_status.models import UserStatus
from .serializers import IDCardSerializer
from .utils import FaceDetector



class IDCardViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        serializer = IDCardSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'ok': False,
                'errors': serializer.errors
            }, status=400)

        username = serializer.validated_data.get('username')
        photo = serializer.validated_data.get('photo')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'message': f'User "{username}" not found'
            }, status=404)
        
        user_status, user_create = UserStatus.objects.get_or_create(user=user)
        
        if user_status.user_idcard_status:
            return Response({
                'ok': False,
                'message': 'ID card already processed for this user',
            }, status=400)
        
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
                }, status=400)
            
            with transaction.atomic():
                IDCard.objects.create(
                    user=user,
                    photo=photo  
                )
                
                user_status.user_idcard_status = True
                user_status.save()
                

                
            return Response({
                'ok': True,
                'username': user.username,
                'message': 'Face detected and ID card processed successfully',
            }, status=200)
            
        except Exception as e:
            return Response({
                'ok': False,
                'message': f'Processing failed: {str(e)}'
            }, status=400)
        
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)