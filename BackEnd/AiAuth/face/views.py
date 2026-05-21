from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .serializers import FaceSerializer
from .utils import  FaceRecognizer , FaceDetector
import face_recognition as fr
from .models import Face
from id_card.models import IDCard
from user_status.models import UserStatus
from django.contrib.auth.models import User



class FaceViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        serializer = FaceSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'ok': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data.get('username')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'message': f'User with username "{username}" not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user_status = UserStatus.objects.get(user=user)
            if user_status.user_face_status:
                return Response({
                    'ok': False,
                    'message': 'This user has already completed the face verification step',
                    'already_processed': True
                }, status=status.HTTP_400_BAD_REQUEST)
        except UserStatus.DoesNotExist:
            pass
        
        try:
            id_card = IDCard.objects.get(user=user)
        except IDCard.DoesNotExist:
            return Response({
                'ok': False,
                'message': 'No ID card found for this user. Please upload ID card first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if Face.objects.filter(user=user).exists():
            return Response({
                'ok': False,
                'message': 'Face already uploaded for this user',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        face_user = serializer.save()
        
        try:

            facecropper = FaceDetector()
            facecropper_status = facecropper.crop_and_save_face(face_user.photo.path)
            

            if facecropper_status == False:
   
                face_user.delete()

                return Response({
                    'ok': False,
                    'message': f'No face found'
                }, status=400)


            encoded = {}
            
            
            id_card_face = fr.load_image_file(id_card.photo.path)
            id_card_encodings = fr.face_encodings(id_card_face)


            
            if not id_card_encodings:
                face_user.delete()
                return Response({
                    'ok': False,
                    'message': 'No face detected in the ID card image'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            encoded[user] = id_card_encodings[0]
            

            facerecognizer = FaceRecognizer(encoded)
            result = facerecognizer.classify_face(face_user.photo.path)
            
            if result == user:
                user_status, created = UserStatus.objects.get_or_create(
                    user=user,
                    defaults={'user_face_status': True, 'user_idcard_status': True}
                )
                if not created:
                    user_status.user_face_status = True
                    user_status.save()
                
                return Response({
                    'ok': True,
                    'username': user.username,
                    'message': 'Faces match successfully. Verification completed.'
                }, status=status.HTTP_200_OK)
            else:
                face_user.delete()
                return Response({
                    'ok': False,
                    'message': 'Faces do not match. The photo does not match the ID card.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:

            if face_user and face_user.pk:
                face_user.delete()


            return Response({
                'ok': False,
                'message': f'Error processing face: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)