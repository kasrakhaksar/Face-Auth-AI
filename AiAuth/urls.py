from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
import AiAuth.settings
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from id_card.views import IDCardViewSet
from face.views import FaceViewSet
from video.views import VideoViewSet
from user_status.views import UserStatusViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="Authentication API",
        default_version='v1',
        description="API documentation for the face authentication ai",
    ),
    public=True,
    permission_classes=(AllowAny,),
    authentication_classes=(),
)

router = DefaultRouter()

router.register(r'api/id_card', IDCardViewSet, basename='id_card')
router.register(r'api/face', FaceViewSet, basename='face')
router.register(r'api/video', VideoViewSet, basename='video')
router.register(r'api/userstatus', UserStatusViewSet, basename='userstatus')

urlpatterns = [
    path('admin/', admin.site.urls),

    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    path('swagger(<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    path('api/id_card/task-status/<str:pk>/', IDCardViewSet.as_view({'get': 'get_task_status'}), name='task-status-idcard'),
    path('api/face/task-status/<str:pk>/', FaceViewSet.as_view({'get': 'get_task_status'}), name='task-status-face'),
    path('api/video/task-status/<str:pk>/', VideoViewSet.as_view({'get': 'get_task_status'}),  name='task-status-video'),

    path('', include(router.urls)),

]

urlpatterns += static(AiAuth.settings.MEDIA_URL, document_root=AiAuth.settings.MEDIA_ROOT)