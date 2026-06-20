from rest_framework.serializers import Serializer,FileField,CharField,ValidationError
import os

class VideoSerializer(Serializer):
    video = FileField()
    randomCheck = CharField(max_length=150)
    

    def validate_video(self, value):
        valid_extensions = [".mp4",".mov",".avi", ".mkv"]
        ext = os.path.splitext(value.name)[1].lower()

        if ext not in valid_extensions:
            raise ValidationError(
                f"Only {', '.join(valid_extensions)} files are allowed"
            )

        max_size = 100 * 1024 * 1024

        if value.size > max_size:
            raise ValidationError(
                "Video size should not exceed 100MB"
            )

        return value

    def validate_randomCheck(self, value):

        if not value:
            raise ValidationError(
                "randomCheck cannot be empty"
            )
        return value.split()