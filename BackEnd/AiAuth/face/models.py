from django.db.models import Model, AutoField, ForeignKey, CASCADE, DateTimeField, ImageField
from django.contrib.auth.models import User
from django.db.models import Index


class Face(Model):
    id = AutoField(primary_key=True)
    user = ForeignKey(User, on_delete=CASCADE, unique=True)
    photo = ImageField(upload_to='faces')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['user']),
            Index(fields=['photo'])
        ]

    def __str__(self):
        return f"{self.user.username} - Face"