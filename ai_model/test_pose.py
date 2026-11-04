import cv2
import mediapipe as mp
import urllib.request
import os
import time
import numpy as np
from utils import calculate_angle

pose_model_path = 'pose_landmarker_lite.task'
hand_model_path = 'hand_landmarker.task'

if not os.path.exists(pose_model_path):
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task", pose_model_path)
if not os.path.exists(hand_model_path):
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task", hand_model_path)


BaseOptions = mp.tasks.BaseOptions
VisionRunningMode = mp.tasks.vision.RunningMode

PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
pose_options = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=pose_model_path), running_mode=VisionRunningMode.VIDEO)

HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
hand_options = HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=hand_model_path), running_mode=VisionRunningMode.VIDEO, num_hands=2)

current_exercise = "SQUATS"
squat_counter = 0
squat_stage = "up"
standing_angle = 170  
is_calibrated = False
calibration_frames = 0

SQUAT_DOWN_THRESHOLD = 100

cap = cv2.VideoCapture(0)

with PoseLandmarker.create_from_options(pose_options) as pose_landmarker, \
     HandLandmarker.create_from_options(hand_options) as hand_landmarker:
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        frame_timestamp_ms = int(time.time() * 1000)

        pose_result = pose_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        
        # Список для хранения текущих ошибок
        errors = []

        if pose_result.pose_landmarks:
            landmarks = pose_result.pose_landmarks[0]
            
            def get_px(lm): return [lm.x, lm.y] 
            def draw_text(text, point, color=(255, 255, 255)):
                px_x = int(point[0] * frame.shape[1])
                px_y = int(point[1] * frame.shape[0])
                cv2.putText(frame, text, (px_x + 10, px_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                        # Углы ног
            r_hip, r_knee, r_ankle = get_px(landmarks[24]), get_px(landmarks[26]), get_px(landmarks[28])
            angle_r_leg = calculate_angle(r_hip, r_knee, r_ankle)
            draw_text(str(int(angle_r_leg)), r_knee, (0, 255, 255))

            l_hip, l_knee, l_ankle = get_px(landmarks[23]), get_px(landmarks[25]), get_px(landmarks[27])
            angle_l_leg = calculate_angle(l_hip, l_knee, l_ankle)
            draw_text(str(int(angle_l_leg)), l_knee, (0, 255, 255))

            avg_knee_angle = (angle_r_leg + angle_l_leg) / 2

            # Берем координаты плеча и бедра
            r_shoulder = get_px(landmarks[12])
            r_hip_pt = get_px(landmarks[24])
            
            # В MediaPipe ось Y идет ВНИЗ. 
            # Разница по X покажет, насколько плечо ушло вперед относительно бедра
            shoulder_x_diff = abs(r_shoulder[0] - r_hip_pt[0])
            
            # Если плечо ушло вперед больше чем на 15% от ширины кадра, значит спина наклонена
            # (Подберите коэффициент 0.15, если срабатывает ложно)
            is_back_bent = shoulder_x_diff > 0.15

            # --- КАЛИБРОВКА ---
            if not is_calibrated:
                if calibration_frames < 30:
                    calibration_frames += 1
                    cv2.putText(frame, "КАЛИБРОВКА... Встаньте ровно!", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                else:
                    standing_angle = avg_knee_angle
                    is_calibrated = True

            if current_exercise == "SQUATS" and is_calibrated:
                
                # 1. Проверка глубины
                if 100 < avg_knee_angle < 140 and squat_stage == "up":
                     errors.append("Сядьте глубже")

                # 2. Проверка спины (Теперь проверяем по наклону, а не по углу)
                if is_back_bent:
                    errors.append("Спину ровнее")

                # 3. Проверка коленей (упрощенная)
                knee_forward = r_knee[0] - r_ankle[0] > 0.1
                if knee_forward and avg_knee_angle < 120:
                    errors.append("Колени не выходят за носки")

                # Логика подсчета
                if avg_knee_angle < SQUAT_DOWN_THRESHOLD:
                    squat_stage = "down"
                
                if avg_knee_angle > (standing_angle - 10) and squat_stage == "down":
                    squat_stage = "up"
                    squat_counter += 1
                    print(f"Приседание: {squat_counter}")

            # Отрисовка скелета
            for landmark in landmarks:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

            connections = mp.tasks.vision.PoseLandmarksConnections.POSE_LANDMARKS
            for connection in connections:
                start_point = (int(landmarks[connection.start].x * frame.shape[1]), int(landmarks[connection.start].y * frame.shape[0]))
                end_point = (int(landmarks[connection.end].x * frame.shape[1]), int(landmarks[connection.end].y * frame.shape[0]))
                cv2.line(frame, start_point, end_point, (255, 0, 255), 2)

        # --- РУКИ ---
        hand_result = hand_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        if hand_result.hand_landmarks:
            for hand_landmarks in hand_result.hand_landmarks:
                for landmark in hand_landmarks:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)

 
        cv2.rectangle(frame, (0, 0), (400, 120), (0, 0, 0), -1)
        
        if current_exercise == "SQUATS":
            cv2.putText(frame, f"Приседания: {squat_counter}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            stage_text = "Присел" if squat_stage == "down" else "Встал"
            stage_color = (0, 0, 255) if squat_stage == "down" else (0, 255, 0)
            cv2.putText(frame, stage_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, stage_color, 2)

        # ВЫВОД ОШИБОК (Красным цветом)
        if errors:
            # Берем первую ошибку из списка для отображения
            error_text = errors[0] 
            cv2.putText(frame, error_text, (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        cv2.putText(frame, "1-Приседания | 2-Отжимания | q-Выход", (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow('CoolCoach - Тренировка', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            current_exercise = "SQUATS"
            is_calibrated = False
            calibration_frames = 0
            squat_counter = 0
        elif key == ord('2'):
            current_exercise = "PUSHUPS"

cap.release()
cv2.destroyAllWindows()