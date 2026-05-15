from rest_framework.serializers import Serializer, CharField, FileField, ListField, ValidationError
from django.contrib.auth.models import User
from .models import Video
import os
import uuid

class VideoSerializer(Serializer):
    username = CharField(max_length=150)
    video = FileField()
    randomCheck = ListField(
        child=CharField(),
        help_text="List of Persian words to check"
    )

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
        if not isinstance(value, list):
            raise ValidationError("randomCheck must be a list")
        
        if len(value) == 0:
            raise ValidationError("randomCheck cannot be empty")
        
        cleaned_words = [word.strip().lower() for word in value]
        return cleaned_words

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
            self.context['user_instance'] = user
            return value
        except User.DoesNotExist:
            raise ValidationError(f'User with username "{value}" does not exist')

    def create(self, validated_data):
        user = self.context.get('user_instance')
        if not user:
            user = User.objects.get(username=validated_data['username'])
        
        video_file = validated_data['video']
        
        file_name = f"video_{user.username}_{uuid.uuid4().hex[:10]}.mp4"
 
        video = Video.objects.create(
            user=user, 
            video=video_file,  

        )
        
        if hasattr(video.video, 'name'):
            old_name = video.video.name
            new_name = f"videos/{file_name}"
            video.video.name = new_name
            video.save()
        
        return video