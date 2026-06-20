from celery import shared_task
from django.contrib.auth.models import User
from django.db import transaction
import face_recognition as fr
import tempfile
import os
from .models import Face
from user_status.models import UserStatus
from id_card.models import IDCard
from .utils import FaceRecognizer, FaceDetector



@shared_task(bind=True)
def process_face_verification(self, user_id, photo_data, photo_name):

    try:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return {
                "ok":False,
                "message":"User not found",
                "status_code":404
            }
        
        try:
            user_status = UserStatus.objects.get(user=user)
            if user_status.user_face_status:
                return {
                    'ok': False,
                    'message': 'This user has already completed the face verification step',
                    'already_processed': True,
                    'status_code': 400
                }
        except UserStatus.DoesNotExist:
            pass
        
        try:
            id_card = IDCard.objects.get(user=user)
        except IDCard.DoesNotExist:
            return {
                'ok': False,
                'message': 'No ID card found for this user. Please upload ID card first.',
                'status_code': 400
            }
        
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(photo_name)[1]) as temp_file:
                temp_file.write(photo_data)
                temp_path = temp_file.name
            
            face_detector = FaceDetector()
            face_detected = face_detector.crop_and_save_face(temp_path)
            
            if not face_detected:
                return {
                    'ok': False,
                    'message': 'No face found in the uploaded image',
                    'status_code': 400
                }
            
            id_card_face = fr.load_image_file(id_card.photo.path)
            id_card_encodings = fr.face_encodings(id_card_face)
            
            if not id_card_encodings:
                return {
                    'ok': False,
                    'message': 'No face detected in the ID card image',
                    'status_code': 400
                }
            
            encoded = {user: id_card_encodings[0]}
            face_recognizer = FaceRecognizer(encoded)
            result = face_recognizer.classify_face(temp_path)
            
            if result != user:
                return {
                    'ok': False,
                    'message': 'Faces do not match. The photo does not match the ID card.',
                    'status_code': 400
                }
            
            with transaction.atomic():
                from django.core.files.base import ContentFile
                face_instance = Face(user=user)
                face_instance.photo.save(photo_name, ContentFile(photo_data))
                face_instance.save()
                
                user_status, created = UserStatus.objects.get_or_create(
                    user=user,
                    defaults={'user_face_status': True, 'user_idcard_status': True}
                )
                if not created:
                    user_status.user_face_status = True
                    user_status.save()
            
            return {
                'ok': True,
                'username': user.username,
                'message': 'Faces match successfully. Verification completed.',
                'status_code': 200
            }
            
        except Exception as e:
            return {
                'ok': False,
                'message': f'Error processing face: {str(e)}',
                'status_code': 400
            }
        
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        return {
            'ok': False,
            'message': f'Unexpected error: {str(e)}',
            'status_code': 500
        }