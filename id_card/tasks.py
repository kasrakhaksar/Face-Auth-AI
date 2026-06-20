from celery import shared_task
from django.contrib.auth.models import User
from django.db import transaction
from django.core.files.base import ContentFile
import tempfile
import os

from .models import IDCard
from user_status.models import UserStatus
from .utils import FaceDetector



@shared_task(bind=True)
def process_id_card_verification(self, user_id, photo_data, photo_name):

    try:
        try:
            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:

            return {
                "ok": False,
                "message": "User not found",
                "status_code": 404
            }

        user_status, created = UserStatus.objects.get_or_create(
            user=user
        )
        if user_status.user_idcard_status:

            return {
                "ok": False,
                "message": "ID card already processed for this user",
                "status_code": 400
            }

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(photo_name)[1]
            ) as temp_file:

                temp_file.write(photo_data)
                temp_path = temp_file.name

            face_detector = FaceDetector()
            face_detected = (
                face_detector
                .crop_and_save_face(temp_path)
            )
            if not face_detected:

                return {
                    "ok": False,
                    "message": "No face found in uploaded image",
                    "status_code": 400
                }

            with transaction.atomic():
                id_card = IDCard(user=user)

                id_card.photo.save(photo_name, ContentFile(photo_data))
                id_card.save()
                user_status.user_idcard_status = True
                user_status.save()

            return {
                "ok": True,
                "user_id": user.id,
                "username": user.username,
                "message":
                    "Face detected and ID card processed successfully",
                "status_code": 200
            }
        except Exception as e:
            return {
                "ok": False,
                "message": f"Processing failed: {str(e)}",
                "status_code": 400
            }

        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        return {
            "ok": False,
            "message":f"Unexpected error: {str(e)}",
            "status_code": 500
        }