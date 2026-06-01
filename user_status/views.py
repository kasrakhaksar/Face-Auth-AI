from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST , HTTP_404_NOT_FOUND , HTTP_200_OK
from django.contrib.auth.models import User
from .models import UserStatus
from .serializers import UserStatusSerializer


class UserStatusViewSet(ViewSet):
    
    def create(self, request):
        username = request.data.get('username')
        
        if not username:
            return Response({
                'ok': False,
                'error': 'username is required'
            }, status=HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
            user_status, _ = UserStatus.objects.get_or_create(user=user)
            serializer = UserStatusSerializer(user_status)
            
            return Response({
                'ok': True,
                'data': serializer.data
            }, status=HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'error': 'User not found'
            }, status=HTTP_404_NOT_FOUND)