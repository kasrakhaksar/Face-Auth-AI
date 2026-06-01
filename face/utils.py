from __future__ import annotations

from typing import Optional
import cv2
import face_recognition as face_rec
import numpy as np


class FaceRecognizer:
    def __init__(
        self,
        known_faces: dict[str, np.ndarray],
    ) -> None:
        self.known_faces: dict[str, np.ndarray] = known_faces
        self._face_encodings: list[np.ndarray] = list(known_faces.values())
        self._known_names: list[str] = list(known_faces.keys())

    def classify_face(
        self,
        image_path: str,
    ) -> str | bool:
        image: np.ndarray = face_rec.load_image_file(image_path)

        try:
            face_locations: list[tuple[int, int, int, int]] = (
                face_rec.face_locations(image)
            )

            unknown_encodings: list[np.ndarray] = (
                face_rec.face_encodings(image, face_locations)
            )

            if not unknown_encodings:
                return False

            detected_names: list[str] = []

            for encoding in unknown_encodings:
                matches: list[bool] = face_rec.compare_faces(
                    self._face_encodings,
                    encoding,
                )

                face_distances: np.ndarray = face_rec.face_distance(
                    self._face_encodings,
                    encoding,
                )

                best_match_index: int = int(np.argmin(face_distances))

                if matches[best_match_index]:
                    person_name: str = self._known_names[best_match_index]
                else:
                    person_name = "UnknownUser"

                detected_names.append(person_name)

            return detected_names[0]

        except Exception:
            return False


class FaceDetector:
    def __init__(
        self,
        scale_factor: float = 1.3,
        min_neighbors: int = 5,
        min_size: tuple[int, int] = (30, 30),
    ) -> None:
        self.scale_factor: float = scale_factor
        self.min_neighbors: int = min_neighbors
        self.min_size: tuple[int, int] = min_size

        self._face_cascade: cv2.CascadeClassifier = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect_face(
        self,
        image_path: str,
    ) -> tuple[
        Optional[np.ndarray],
        Optional[tuple[int, int, int, int]]
    ]:
        image = cv2.imread(image_path)

        if image is None:
            return None, None

        grayscale: np.ndarray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        detected_faces = self._face_cascade.detectMultiScale(
            grayscale,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size,
        )

        if len(detected_faces) == 0:
            return None, None

        x, y, width, height = map(int, detected_faces[0])

        face_region: np.ndarray = image[
            y:y + height,
            x:x + width,
        ]

        bounding_box: tuple[int, int, int, int] = (
            x,
            y,
            width,
            height,
        )

        return face_region, bounding_box

    def crop_and_save_face(
        self,
        image_path: str,
        output_path: str | None = None,
    ) -> bool:
        if output_path is None:
            output_path = image_path

        face_region, _ = self.detect_face(image_path)

        if face_region is not None:
            cv2.imwrite(output_path, face_region)
            return True

        return False