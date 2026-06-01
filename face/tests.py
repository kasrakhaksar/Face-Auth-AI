from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile

from PIL import Image
import tempfile


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

        self.url = "/face/"
        self.photo = get_test_image()


    @patch("face.views.process_face_verification.delay")
    def test_create_face_task(self, mock_delay):

        mock_task = MagicMock()
        mock_task.id = "face-task-id"
        mock_delay.return_value = mock_task

        response = self.client.post(self.url, {
            "username": "testuser",
            "photo": self.photo
        }, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["ok"], True)
        self.assertEqual(response.data["task_id"], "face-task-id")


    @patch("face.views.AsyncResult")
    def test_task_status_pending(self, mock_async):

        mock_obj = MagicMock()
        mock_obj.state = "PENDING"
        mock_async.return_value = mock_obj

        response = self.client.get("/face/fake-id/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "PENDING")
        self.assertIn("status", response.data)


    @patch("face.views.AsyncResult")
    def test_task_status_success(self, mock_async):

        mock_obj = MagicMock()
        mock_obj.state = "SUCCESS"
        mock_obj.result = {
            "ok": True,
            "similarity": 0.92
        }
        mock_async.return_value = mock_obj

        response = self.client.get("/face/fake-id/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "SUCCESS")
        self.assertEqual(response.data["result"]["ok"], True)


    @patch("face.views.AsyncResult")
    def test_task_status_failure(self, mock_async):

        mock_obj = MagicMock()
        mock_obj.state = "FAILURE"
        mock_obj.info = "face not detected"
        mock_async.return_value = mock_obj

        response = self.client.get("/face/fake-id/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "FAILURE")
        self.assertIn("status", response.data)