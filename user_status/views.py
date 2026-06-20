from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_200_OK

from .models import UserStatus
from .serializers import UserStatusSerializer


class UserStatusViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        user = request.user
        user_status, _ = UserStatus.objects.get_or_create(user=user)
        serializer = UserStatusSerializer(user_status)

        return Response(
            {
                "ok": True,
                "data": serializer.data
            },
            status=HTTP_200_OK
        )