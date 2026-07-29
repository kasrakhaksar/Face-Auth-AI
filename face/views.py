from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import FaceSerializer
from .tasks import process_face_verification
from user_status.models import VerificationTask
from AiAuth.mixins import TaskStatusMixin


class FaceViewSet(TaskStatusMixin, ViewSet):

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    task_type = 'face'
    throttle_scope = 'face_upload'

    def get_throttles(self):
        if self.action == 'create':
            return super().get_throttles()
        return []

    def create(self, request):
        serializer = FaceSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "ok": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        photo = serializer.validated_data["photo"]
        user = request.user

        photo_data = photo.read()
        photo_name = photo.name

        task = process_face_verification.delay(
            user.id,
            photo_data,
            photo_name
        )

        VerificationTask.objects.create(
            task_id=task.id,
            user=user,
            task_type='face'
        )

        return Response(
            {
                "ok": True,
                "task_id": task.id,
                "message": "Face verification is being processed"
            },
            status=status.HTTP_202_ACCEPTED
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="status"
    )
    def get_task_status(self, request, pk=None):
        return self.get_task_status_response(request, pk)