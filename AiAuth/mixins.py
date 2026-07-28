from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult

from user_status.models import VerificationTask


class TaskStatusMixin:
    task_type = None

    def get_task_status_response(self, request, pk):

        owns_task = VerificationTask.objects.filter(
            task_id=pk,
            user=request.user,
            task_type=self.task_type
        ).exists()

        if not owns_task:
            return Response(
                {
                    "ok": False,
                    "state": None,
                    "message": "Task not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        task_result = AsyncResult(pk)

        if task_result.state == "PENDING":
            return Response(
                {
                    "ok": None,
                    "state": task_result.state,
                    "message": "Task is pending"
                }
            )

        if task_result.state == "FAILURE":
            return Response(
                {
                    "ok": False,
                    "state": task_result.state,
                    "message": str(task_result.info)
                }
            )

        if task_result.state == "SUCCESS":
            result = task_result.result
            return Response(
                {
                    "ok": result.get("ok", False),
                    "state": task_result.state,
                    "result": result
                }
            )

        return Response(
            {
                "ok": None,
                "state": task_result.state,
                "message": "Processing"
            }
        )