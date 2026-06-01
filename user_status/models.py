from django.db.models import Model, AutoField, ForeignKey, CASCADE, DateTimeField , BooleanField
from django.contrib.auth.models import User
from django.db.models import Index


class UserStatus(Model):
    id = AutoField(primary_key=True)
    user = ForeignKey(User, on_delete=CASCADE, unique=True)
    user_face_status = BooleanField(default=False)
    user_idcard_status = BooleanField(default=False)
    user_video_status = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['user'])
        ]

    def __str__(self):
        return f"{self.user.username} - Status"