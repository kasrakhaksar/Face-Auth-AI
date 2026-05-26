from rest_framework.serializers import Serializer, CharField, FileField, ValidationError
from django.contrib.auth.models import User
import os



class VideoSerializer(Serializer):
    username = CharField(max_length=150)
    video = FileField()
    randomCheck = CharField(max_length=150)


    def validate_video(self, value):
        valid_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError(f"Only {', '.join(valid_extensions)} files are allowed")
        
        max_size = 100 * 1024 * 1024
        if value.size > max_size:
            raise ValidationError(f"Video size should not exceed {max_size // (1024*1024)}MB")
        
        return value

    def validate_randomCheck(self, value):
        if not isinstance(value, str):
            raise ValidationError("randomCheck must be a string")
        
        if len(value) == 0:
            raise ValidationError("randomCheck cannot be empty")
        
        randomCheck = value.split()
        return randomCheck
        
    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
            self.context['user_instance'] = user
            return value
        except User.DoesNotExist:
            raise ValidationError(f'User with username "{value}" does not exist')