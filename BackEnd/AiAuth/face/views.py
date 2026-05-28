from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from celery.result import AsyncResult
from .serializers import FaceSerializer
from .tasks import process_face_verification



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
        photo = serializer.validated_data.get('photo')
        
        photo_data = photo.read()
        photo_name = photo.name
        
        task = process_face_verification.delay(username, photo_data, photo_name)
        
        return Response({
            'ok': True,
            'task_id': task.id,
            'message': 'Face verification is being processed. Use the task ID to check status.'
        }, status=status.HTTP_202_ACCEPTED)
    
    
    def get_task_status(self, request, task_id):

        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'state': task_result.state,
                'status': 'Task is pending...'
            }
        elif task_result.state == 'FAILURE':
            response = {
                'state': task_result.state,
                'status': str(task_result.info),
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            response = {
                'state': task_result.state,
                'result': result
            }
        else:
            response = {
                'state': task_result.state,
                'status': 'Task is processing...'
            }
        
        return Response(response)