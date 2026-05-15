from rest_framework.serializers import Serializer, CharField, ImageField, ValidationError
from django.contrib.auth.models import User
from .models import Face
import os


class FaceSerializer(Serializer):
    username = CharField(max_length=150)
    photo = ImageField()

    def validate_photo(self, value):
        if value.size > 5 * 1024 * 1024:  
            raise ValidationError("Image size should not exceed 5MB")
        
        valid_extensions = ['.jpg', '.jpeg', '.png']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError("Only JPG and PNG files are allowed")
        
        return value

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
        
        return Face.objects.create(
            user=user, 
            photo=validated_data['photo']
        )