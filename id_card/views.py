from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.conf import settings

from .serializers import IDCardSerializer
from .tasks import process_id_card_verification
from user_status.models import VerificationTask
from AiAuth.mixins import TaskStatusMixin


class IDCardViewSet(TaskStatusMixin, ViewSet):

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    task_type = 'id_card'
    throttle_scope = 'id_card_upload'

    def get_throttles(self):
        if self.action == 'create':
            return super().get_throttles()
        return []

    def create(self, request):

        serializer = IDCardSerializer(
            data=request.data
        )
        if not serializer.is_valid():

            return Response(
                {
                    "ok":False,
                    "errors":serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        photo = serializer.validated_data["photo"]
        user = request.user

        photo_data = photo.read()
        photo_name = photo.name

        if getattr(settings,"CELERY_TASK_ALWAYS_EAGER", False):

            result = process_id_card_verification(
                user.id,
                photo_data,
                photo_name
            )
            return Response(
                {
                    k:v 
                    for k,v in result.items()
                    if k != "status_code"
                },
                status=result.get(
                    "status_code",
                    status.HTTP_200_OK
                )
            )

        task = process_id_card_verification.delay(
            user.id,
            photo_data,
            photo_name
        )

        VerificationTask.objects.create(
            task_id=task.id,
            user=user,
            task_type='id_card'
        )

        return Response(
            {
                "ok":True,
                "task_id":task.id,
                "message":"Processing started"
            },
            status=status.HTTP_202_ACCEPTED
        )


    @action(detail=True ,methods=["get"], url_path="status")
    def get_task_status(self, request, pk=None):
        return self.get_task_status_response(request, pk)