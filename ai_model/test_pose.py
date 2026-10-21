import cv2
import mediapipe as mp
import urllib.request
import os
import time

pose_model_path = 'pose_landmarker_lite.task'
hand_model_path = 'hand_landmarker.task'

if not os.path.exists(pose_model_path):
    print("Скачиваем модель тела...")
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task", pose_model_path)

if not os.path.exists(hand_model_path):
    print("Скачиваем модель рук...")
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task", hand_model_path)

print("Модели готовы. Запускаем камеру...")

BaseOptions = mp.tasks.BaseOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Настройка для тела
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
pose_options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=pose_model_path),
    running_mode=VisionRunningMode.VIDEO
)

# Настройка для рук
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
hand_options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=hand_model_path),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=2 # Максимум 2 руки
)

# Включаем камеру
cap = cv2.VideoCapture(0)

with PoseLandmarker.create_from_options(pose_options) as pose_landmarker, \
     HandLandmarker.create_from_options(hand_options) as hand_landmarker:
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Отражаем кадр как в зеркале
        frame = cv2.flip(frame, 1)
        
        # Конвертируем цвета для MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        frame_timestamp_ms = int(time.time() * 1000)

        # --- Распознавание ТЕЛА ---
        pose_result = pose_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        
        if pose_result.pose_landmarks:
            landmarks = pose_result.pose_landmarks[0]
            
            # Рисуем точки тела
            for landmark in landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 3, (0, 255, 0), -1) # Зеленые

            # Рисуем линии скелета
            connections = mp.tasks.vision.PoseLandmarksConnections.POSE_LANDMARKS
            for connection in connections:
                start_idx = connection.start
                end_idx = connection.end
                
                start_point = (int(landmarks[start_idx].x * frame.shape[1]), int(landmarks[start_idx].y * frame.shape[0]))
                end_point = (int(landmarks[end_idx].x * frame.shape[1]), int(landmarks[end_idx].y * frame.shape[0]))
                
                cv2.line(frame, start_point, end_point, (255, 0, 255), 2) # Фиолетовые линии

        # --- Распознавание РУК ---
        hand_result = hand_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        
        if hand_result.hand_landmarks:
            for hand_landmarks in hand_result.hand_landmarks:
                # Рисуем суставы пальцев
                for landmark in hand_landmarks:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 4, (0, 0, 255), -1) # Синие точки для рук

                # Рисуем линии на руках (соединяем костяшки)
                # В новой API связи для рук лежат в HandLandmarksConnections
                hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
                for connection in hand_connections:
                    start_idx = connection.start
                    end_idx = connection.end
                    
                    start_point = (int(hand_landmarks[start_idx].x * frame.shape[1]), int(hand_landmarks[start_idx].y * frame.shape[0]))
                    end_point = (int(hand_landmarks[end_idx].x * frame.shape[1]), int(hand_landmarks[end_idx].y * frame.shape[0]))
                    
                    cv2.line(frame, start_point, end_point, (255, 255, 0), 2) # Желтые линии на руках

        cv2.imshow('CoolCoach - Full Skeleton', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()