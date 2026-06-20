from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from PIL import Image
import tempfile
from rest_framework_simplejwt.tokens import RefreshToken


def get_test_image():
    image = Image.new("RGB", (100, 100), color="red")

    tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")

    image.save(tmp_file, format="JPEG")

    tmp_file.seek(0)

    return SimpleUploadedFile(
        "test.jpg",
        tmp_file.read(),
        content_type="image/jpeg"
    )


class IDCardViewSetTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="123456"
        )

        refresh = RefreshToken.for_user(self.user)

        self.access_token = str(refresh.access_token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.url = "/api/id_card/"
        self.photo = get_test_image()


    @patch("id_card.views.process_id_card_verification")
    def test_create_eager_execution(self, mock_task):

        mock_task.return_value = {
            "ok": True,
            "status_code": 200,
            "message": "done"
        }

        with self.settings(CELERY_TASK_ALWAYS_EAGER=True):
            response = self.client.post(
                self.url,
                {
                    "photo": self.photo
                },
                format="multipart"
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["ok"])


    @patch("id_card.views.process_id_card_verification.delay")
    def test_create_async_task(self, mock_delay):

        mock_task = MagicMock()
        mock_task.id = "fake-task-id"

        mock_delay.return_value = mock_task

        with self.settings(CELERY_TASK_ALWAYS_EAGER=False):
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

        self.assertEqual(
            response.data["task_id"],
            "fake-task-id"
        )


    @patch("id_card.views.AsyncResult")
    def test_task_status_pending(self, mock_async):

        mock_obj = MagicMock()
        mock_obj.state = "PENDING"

        mock_async.return_value = mock_obj

        response = self.client.get(
            "/api/id_card/fake-id/status/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "PENDING")
        self.assertIsNone(response.data["ok"])


    @patch("id_card.views.AsyncResult")
    def test_task_status_success(self, mock_async):

        mock_obj = MagicMock()

        mock_obj.state = "SUCCESS"
        mock_obj.result = {
            "ok": True,
            "data": "verified"
        }

        mock_async.return_value = mock_obj

        response = self.client.get(
            "/api/id_card/fake-id/status/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["ok"])
        self.assertEqual(response.data["state"], "SUCCESS")


    @patch("id_card.views.AsyncResult")
    def test_task_status_failure(self, mock_async):

        mock_obj = MagicMock()

        mock_obj.state = "FAILURE"
        mock_obj.info = "error occurred"

        mock_async.return_value = mock_obj

        response = self.client.get(
            "/api/id_card/fake-id/status/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "FAILURE")
        self.assertFalse(response.data["ok"])