from rest_framework.serializers import ModelSerializer , CharField
from .models import UserStatus

class UserStatusSerializer(ModelSerializer):
    username = CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserStatus
        fields = ['username', 'user_idcard_status', 'user_face_status', 'user_video_status']