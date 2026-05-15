from rest_framework.serializers import Serializer, CharField, ImageField , ValidationError
from django.contrib.auth.models import User
from .models import IDCard

class IDCardSerializer(Serializer):
    username = CharField()
    photo = ImageField()

    def create(self, validated_data):
        username = validated_data['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise ValidationError(f'User with username "{username}" does not exist')
        
        return IDCard.objects.create(
            user=user, 
            photo=validated_data['photo']
        )