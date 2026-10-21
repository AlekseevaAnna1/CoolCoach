import cv2
import mediapipe as mp
import urllib.request
import os
import time
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


current_exercise = "SQUATS" # По умолчанию приседания

squat_counter = 0
squat_stage = "up"

pushup_counter = 0
pushup_stage = "up"

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
        
        if pose_result.pose_landmarks:
            landmarks = pose_result.pose_landmarks[0]
            
            def get_px(lm): return [lm.x, lm.y] 
            def draw_text(text, point, color=(255, 255, 255)):
                px_x = int(point[0] * frame.shape[1])
                px_y = int(point[1] * frame.shape[0])
                cv2.putText(frame, text, (px_x + 10, px_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # Углы рук
            r_sh, r_el, r_wr = get_px(landmarks[12]), get_px(landmarks[14]), get_px(landmarks[16])
            angle_r_arm = calculate_angle(r_sh, r_el, r_wr)
            draw_text(str(int(angle_r_arm)), r_el, (255, 255, 0))

            l_sh, l_el, l_wr = get_px(landmarks[11]), get_px(landmarks[13]), get_px(landmarks[15])
            angle_l_arm = calculate_angle(l_sh, l_el, l_wr)
            draw_text(str(int(angle_l_arm)), l_el, (255, 255, 0))

            # Углы ног
            r_hip, r_knee, r_ankle = get_px(landmarks[24]), get_px(landmarks[26]), get_px(landmarks[28])
            angle_r_leg = calculate_angle(r_hip, r_knee, r_ankle)
            draw_text(str(int(angle_r_leg)), r_knee, (0, 255, 255))

            l_hip, l_knee, l_ankle = get_px(landmarks[23]), get_px(landmarks[25]), get_px(landmarks[27])
            angle_l_leg = calculate_angle(l_hip, l_knee, l_ankle)
            draw_text(str(int(angle_l_leg)), l_knee, (0, 255, 255))

            if current_exercise == "SQUATS":
                # Берем среднее значение углов коленей
                avg_knee_angle = (angle_r_leg + angle_l_leg) / 2
                
                if avg_knee_angle < 100:
                    squat_stage = "down"
                if avg_knee_angle > 160 and squat_stage == "down":
                    squat_stage = "up"
                    squat_counter += 1
                    print(f"Приседание: {squat_counter}")

            elif current_exercise == "PUSHUPS":
                # Берем среднее значение углов локтей
                avg_elbow_angle = (angle_r_arm + angle_l_arm) / 2
                
                if avg_elbow_angle < 90:
                    pushup_stage = "down"
                if avg_elbow_angle > 160 and pushup_stage == "down":
                    pushup_stage = "up"
                    pushup_counter += 1
                    print(f"Отжимание: {pushup_counter}")

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

        # --- РУКИ (Медиапайп) ---
        hand_result = hand_landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        if hand_result.hand_landmarks:
            for hand_landmarks in hand_result.hand_landmarks:
                for landmark in hand_landmarks:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 4, (0, 0, 255), -1)


        # Черный фон для текста
        cv2.rectangle(frame, (0, 0), (350, 100), (0, 0, 0), -1)
        
        if current_exercise == "SQUATS":
            cv2.putText(frame, "Упражнение: ПРИСЕДАНИЯ", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Счет: {squat_counter}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            stage_text = "Присел" if squat_stage == "down" else "Встал"
            stage_color = (0, 0, 255) if squat_stage == "down" else (0, 255, 0)
        else:
            cv2.putText(frame, "Упражнение: ОТЖИМАНИЯ", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Счет: {pushup_counter}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            stage_text = "Внизу" if pushup_stage == "down" else "Вверху"
            stage_color = (0, 0, 255) if pushup_stage == "down" else (0, 255, 0)
            
        cv2.putText(frame, stage_text, (200, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, stage_color, 2)

        # Подсказка внизу экрана
        cv2.putText(frame, "Нажмите '1' для Приседаний, '2' для Отжиманий, 'q' для выхода", (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow('CoolCoach - Тренировка', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            current_exercise = "SQUATS"
        elif key == ord('2'):
            current_exercise = "PUSHUPS"

cap.release()
cv2.destroyAllWindows()