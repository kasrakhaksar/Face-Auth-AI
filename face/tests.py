from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from PIL import Image
import tempfile
from rest_framework_simplejwt.tokens import RefreshToken


def get_test_image():
    image = Image.new("RGB", (100, 100), color="blue")

    tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")

    image.save(tmp_file, format="JPEG")

    tmp_file.seek(0)

    return SimpleUploadedFile(
        "test.jpg",
        tmp_file.read(),
        content_type="image/jpeg"
    )


class FaceViewSetTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="123456"
        )

        token = RefreshToken.for_user(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
        )

        self.url = "/api/face/"
        self.photo = get_test_image()


    @patch("face.views.process_face_verification.delay")
    def test_create_face_task(self, mock_delay):

        task = MagicMock()
        task.id = "face-task-id"

        mock_delay.return_value = task

        response = self.client.post(
            self.url,
            {
                "photo": self.photo
            },
            format="multipart"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED
        )

        self.assertTrue(response.data["ok"])

        self.assertEqual(
            response.data["task_id"],
            "face-task-id"
        )