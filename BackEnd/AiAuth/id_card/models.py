from django.db.models import Model, AutoField, ForeignKey, CASCADE, DateTimeField, ImageField
from django.contrib.auth.models import User
from django.db.models import Index
import os
import uuid



def user_idcard_path(instance, filename):
    username = instance.user.username
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        ext = '.png'
    
    new_filename = f"idcard_{uuid.uuid4().hex[:10]}{ext}"
    
    return os.path.join(username, new_filename)



class IDCard(Model):
    id = AutoField(primary_key=True)
    user = ForeignKey(User, on_delete=CASCADE, unique=True)
    photo = ImageField(blank=True, upload_to=user_idcard_path)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            Index(fields=['user']),
            Index(fields=['photo'])
        ]

    def __str__(self):
        return f"{self.user.username} - IDCard"

    def delete(self, *args, **kwargs):
        if self.photo:
            if os.path.isfile(self.photo.path):
                os.remove(self.photo.path)
        
        super().delete(*args, **kwargs)