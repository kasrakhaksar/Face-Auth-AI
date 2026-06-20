from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework_simplejwt.tokens import RefreshToken
import tempfile


def get_test_video():
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4")

    tmp.write(b"fake-video-content")
    tmp.seek(0)

    return SimpleUploadedFile(
        "test.mp4",
        tmp.read(),
        content_type="video/mp4"
    )


class VideoViewSetTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="123456"
        )

        token = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
        )

        self.url = "/api/video/"
        self.video = get_test_video()


    @patch("video.views.process_video_verification.delay")
    def test_create_video_task(self, mock_delay):

        task = MagicMock()
        task.id = "video-task-id"

        mock_delay.return_value = task

        response = self.client.post(
            self.url,
            {
                "video": self.video,
                "randomCheck": "word1 word2 word3"
            },
            format="multipart"
        )

        self.assertEqual(
            response.status_code,
            202
        )

        self.assertTrue(
            response.data["ok"]
        )


    def test_without_jwt(self):

        self.client.credentials()

        response = self.client.post(
            self.url,
            {
                "video": self.video,
                "randomCheck": "a b"
            },
            format="multipart"
        )

        self.assertEqual(
            response.status_code,
            401
        )