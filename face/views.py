from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from celery.result import AsyncResult

from .serializers import FaceSerializer
from .tasks import process_face_verification


class FaceViewSet(ViewSet):

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

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

        task_result = AsyncResult(pk)

        if task_result.state == "PENDING":
            return Response(
                {
                    "state": task_result.state,
                    "status": "Task is pending"
                }
            )

        if task_result.state == "FAILURE":
            return Response(
                {
                    "state": task_result.state,
                    "status": str(task_result.info)
                }
            )

        if task_result.state == "SUCCESS":
            return Response(
                {
                    "state": task_result.state,
                    "result": task_result.result
                }
            )

        return Response(
            {
                "state": task_result.state,
                "status": "Processing"
            }
        )