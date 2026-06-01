from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
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

        self.url = "/video/"
        self.video = get_test_video()

    @patch("video.views.process_video_verification.delay")
    def test_create_video_task(self, mock_delay):

        mock_task = MagicMock()
        mock_task.id = "video-task-id"
        mock_delay.return_value = mock_task

        response = self.client.post(self.url, {
            "username": "testuser",
            "video": self.video,
            "randomCheck": "word1 word2 word3"
        }, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(response.data["ok"])
        self.assertEqual(response.data["task_id"], "video-task-id")


    @patch("video.views.AsyncResult")
    def test_task_status_pending(self, mock_async):

        mock_obj = MagicMock()
        mock_obj.state = "PENDING"
        mock_async.return_value = mock_obj

        response = self.client.get(f"{self.url}fake-id/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "PENDING")
        self.assertIsNone(response.data["ok"])


    @patch("video.views.AsyncResult")
    def test_task_status_success(self, mock_async):

        mock_obj = MagicMock()
        mock_obj.state = "SUCCESS"
        mock_obj.result = {
            "ok": True,
            "frames": 120
        }
        mock_async.return_value = mock_obj

        response = self.client.get(f"{self.url}fake-id/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "SUCCESS")
        self.assertTrue(response.data["ok"])


    @patch("video.views.AsyncResult")
    def test_task_status_failure(self, mock_async):

        mock_obj = MagicMock()
        mock_obj.state = "FAILURE"
        mock_obj.info = "video corrupted"
        mock_async.return_value = mock_obj

        response = self.client.get(f"{self.url}fake-id/status/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "FAILURE")
        self.assertFalse(response.data["ok"])