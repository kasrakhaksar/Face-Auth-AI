"""
URL configuration for AiAuth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path , include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
import AiAuth.settings
from django.urls import path
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


from id_card.views import IDCardViewSet
from face.views import FaceViewSet
from video.views import VideoViewSet
from user_status.views import UserStatusViewSet



schema_view = get_schema_view(
    openapi.Info(
        title="Ai API",
        default_version='v1',
        description="API documentation for the ai project",
    ),
    public=True,
    permission_classes=(IsAuthenticatedOrReadOnly,),
)

router = DefaultRouter()


router.register(r'id_card', IDCardViewSet , basename='id_card')
router.register(r'face', FaceViewSet , basename='face')
router.register(r'video', VideoViewSet , basename='video')
router.register(r'userstatus', UserStatusViewSet , basename='userstatus')



urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger(<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    path('', include(router.urls))
] + static(AiAuth.settings.MEDIA_URL, document_root=AiAuth.settings.MEDIA_ROOT)