from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from celery.result import AsyncResult
from django.conf import settings

from .serializers import IDCardSerializer
from .tasks import process_id_card_verification


class IDCardViewSet(ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    permission_classes = [IsAuthenticated]

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

        task_result = AsyncResult(pk)
        if task_result.state == "PENDING":
            return Response(
                {
                    "state":task_result.state,
                    "status":"Task is pending",
                    "ok":None
                }
            )

        if task_result.state == "FAILURE":
            return Response(
                {
                    "state":task_result.state,
                    "status":str(task_result.info),
                    "ok":False
                }
            )
        if task_result.state == "SUCCESS":
            result = task_result.result
            return Response(
                {
                    "state":task_result.state,
                    "result":result,
                    "ok":result.get(
                        "ok",
                        False
                    )
                }
            )
        return Response(
            {
                "state":task_result.state,
                "status":"Processing",
                "ok":None
            }
        )