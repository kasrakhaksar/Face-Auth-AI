from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from user_status.models import UserStatus
from .utils import FaceDetector
from .serializers import IDCardSerializer
from django.contrib.auth.models import User
import os



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
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'message': f'User "{username}" not found'
            }, status=404)
        
        user_status, created = UserStatus.objects.get_or_create(user=user)
        
        if user_status.user_idcard_status:
            return Response({
                'ok': False,
                'message': 'ID card already processed for this user',
            }, status=400)
        
        id_card = serializer.save()
        
        try:

            facecropper = FaceDetector()
            facecropper.crop_and_save_face(id_card.photo.path)
            
            user_status.user_idcard_status = True
            user_status.save()
            
            return Response({
                'ok': True,
                'username': id_card.user.username,
                'message': 'Face detected and ID card processed successfully'
            })
        
        except Exception as e:
            id_card.delete()

            try:
                os.remove(id_card.photo.path)
            except:
                pass


            return Response({
                'ok': False,
                'message': f'Face detection failed: {str(e)}'
            }, status=400)