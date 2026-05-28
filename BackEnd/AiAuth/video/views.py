from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from celery.result import AsyncResult
from django.conf import settings
from .serializers import VideoSerializer
from .tasks import process_video_verification


class VideoViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        serializer = VideoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'ok': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        username = validated_data.get('username')
        random_words_check = validated_data.get('randomCheck')
        video_file = validated_data.get('video')
        
        video_data = video_file.read()
        video_name = video_file.name
        
        if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
            result = process_video_verification(username, random_words_check, video_data, video_name)
            return Response(
                {k: v for k, v in result.items() if k != 'status_code'}, 
                status=result.get('status_code', status.HTTP_200_OK)
            )
        else:
            task = process_video_verification.delay(username, random_words_check, video_data, video_name)
            return Response({
                'ok': True,
                'task_id': task.id,
                'message': 'Video verification is being processed. Use the task ID to check status.'
            }, status=status.HTTP_202_ACCEPTED)
    
    
    def get_task_status(self, request, task_id):

        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'state': task_result.state,
                'status': 'Task is pending...',
                'ok': None
            }
        elif task_result.state == 'FAILURE':
            response = {
                'state': task_result.state,
                'status': str(task_result.info),
                'ok': False
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            response = {
                'state': task_result.state,
                'result': result,
                'ok': result.get('ok', False)
            }
        else:
            response = {
                'state': task_result.state,
                'status': 'Task is processing...',
                'ok': None
            }
        
        return Response(response)