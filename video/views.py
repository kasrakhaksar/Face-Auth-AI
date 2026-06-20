from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from celery.result import AsyncResult
from django.conf import settings

from .serializers import VideoSerializer
from .tasks import process_video_verification


class VideoViewSet(ViewSet):

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = VideoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "ok": False,
                    "errors": serializer.errors
                },
                status=400
            )

        video = serializer.validated_data["video"]
        random_words = serializer.validated_data["randomCheck"]

        user = request.user

        video_data = video.read()
        video_name = video.name

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):

            result = process_video_verification(
                user.id,
                random_words,
                video_data,
                video_name
            )

            return Response(
                {
                    k: v
                    for k, v in result.items()
                    if k != "status_code"
                },
                status=result.get(
                    "status_code",
                    200
                )
            )

        task = process_video_verification.delay(
            user.id,
            random_words,
            video_data,
            video_name
        )

        return Response(
            {
                "ok": True,
                "task_id": task.id,
                "message": "Video verification is being processed"
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
                    "state": "PENDING",
                    "status": "Task is pending",
                    "ok": None
                }
            )

        if task_result.state == "FAILURE":
            return Response(
                {
                    "state": "FAILURE",
                    "status": str(task_result.info),
                    "ok": False
                }
            )

        if task_result.state == "SUCCESS":
            return Response(
                {
                    "state": "SUCCESS",
                    "result": task_result.result,
                    "ok": task_result.result.get(
                        "ok",
                        False
                    )
                }
            )

        return Response(
            {
                "state": task_result.state,
                "status": "Processing",
                "ok": None
            }
        )