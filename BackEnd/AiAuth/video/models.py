from django.db.models import Model , AutoField , CASCADE , ForeignKey , FileField , DateTimeField 
from django.contrib.auth.models import User
from django.db.models import Index
import os

class Video(Model):
    id = AutoField(primary_key=True)
    user = ForeignKey(User, on_delete=CASCADE, unique=True)
    video_field = FileField(upload_to='videos')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['user']),
            Index(fields=['video_field'])
        ]

    def __str__(self):
        return f"{self.user.username} - Video"
    

    def delete(self, *args, **kwargs):
        if self.video_field:
            if os.path.isfile(self.video_field.path):
                os.remove(self.video_field.path)
        
        super().delete(*args, **kwargs)