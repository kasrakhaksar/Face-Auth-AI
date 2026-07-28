from django.db.models import Model, AutoField, ForeignKey, CASCADE, DateTimeField, BooleanField, CharField
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


class VerificationTask(Model):
    TASK_TYPE_CHOICES = [
        ('face', 'Face'),
        ('id_card', 'ID Card'),
        ('video', 'Video'),
    ]

    id = AutoField(primary_key=True)
    task_id = CharField(max_length=255, unique=True, db_index=True)
    user = ForeignKey(User, on_delete=CASCADE, related_name='verification_tasks')
    task_type = CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            Index(fields=['task_id']),
            Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.task_type} - {self.task_id}"