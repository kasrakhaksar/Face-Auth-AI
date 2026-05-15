import cv2


class FaceDetector:    
    def __init__(self, scale_factor=1.3, min_neighbors=5, min_size=(30, 30)):
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def detect_face(self, image_path):

        image = cv2.imread(image_path)
        
        if image is None:
            return None, None
            
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detected_faces = self._face_cascade.detectMultiScale(
            grayscale,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size
        )
        
        if len(detected_faces) == 0:
            return None, None
        
        x, y, width, height = detected_faces[0]
        face_region = image[y:y+height, x:x+width]
        bounding_box = (x, y, width, height)
        
        return face_region, bounding_box
    
    def crop_and_save_face(self, image_path, output_path=None):
        if output_path is None:
            output_path = image_path
            
        face_region, _ = self.detect_face(image_path)
        
        if face_region is not None:
            cv2.imwrite(output_path, face_region)
            return True
            
        return False