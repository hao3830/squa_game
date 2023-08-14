import cv2
import numpy as np
import mediapipe as mp

from mediapipe import solutions
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2

WEIGHT_PATH = "resource/pose_landmarker.task"

class PoseLandmarker:
    def __init__(self):
        base_options = python.BaseOptions(model_asset_path=WEIGHT_PATH)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options)
        self.detector = vision.PoseLandmarker.create_from_options(options)

    @staticmethod
    def draw_landmarks_on_image(rgb_image, detection_result):
        pose_landmarks_list = detection_result.pose_landmarks
        annotated_image = np.copy(rgb_image)

        # Loop through the detected poses to visualize.
        for idx in range(len(pose_landmarks_list)):
            pose_landmarks = pose_landmarks_list[idx]
            # hip = result.pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP.value].x

            # Draw the pose landmarks.
            pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            pose_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
            ])
            solutions.drawing_utils.draw_landmarks(
            annotated_image,
            pose_landmarks_proto,
            solutions.pose.POSE_CONNECTIONS,
            solutions.drawing_styles.get_default_pose_landmarks_style())
        return annotated_image
    
    def predict(self,frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        detection_result = self.detector.detect(image)
        
        return detection_result

    @staticmethod
    def calculate_angle(a,b,c):
        a = np.array(a) # First
        b = np.array(b) # Miqqqqqd
        c = np.array(c) # End
    
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
    
        if angle >180.0:
            angle = 360-angle
        
        return angle
    
    @staticmethod
    def is_in_roi(roi_bb, point):
        return point[0] > roi_bb[0] and point[1] > roi_bb[1] and point[0] < roi_bb[2] and point[1] < roi_bb[3]