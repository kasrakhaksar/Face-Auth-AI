from rest_framework.serializers import Serializer, ImageField, ValidationError
import os

class FaceSerializer(Serializer):
    photo = ImageField()

    def validate_photo(self, value):

        if value.size > 5 * 1024 * 1024:
            raise ValidationError(
                "Image size should not exceed 5MB"
            )

        valid_extensions = [".jpg",".jpeg",".png"]
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError(
                "Only JPG and PNG files are allowed"
            )
        return value