import cv2
import mediapipe as mp
import urllib.request
import os
import time
import numpy as np

from exercises import Squat, PushUp, Lunge, GluteBridge
from llm_agent import get_feedback
from tts_agent import speak

# ==========================================
# 1. СКАЧИВАНИЕ МОДЕЛЕЙ
# ==========================================
os.makedirs('ai_model/models', exist_ok=True)
pose_model_path = 'ai_model/models/pose_landmarker_lite.task'

if not os.path.exists(pose_model_path):
    print("Скачиваем модель...")
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task", pose_model_path)

BaseOptions = mp.tasks.BaseOptions
VisionRunningMode = mp.tasks.vision.RunningMode
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=pose_model_path),
    running_mode=VisionRunningMode.VIDEO
)

# ==========================================
# 2. МЕНЮ
# ==========================================
print("=== CoolCoach ML Module ===")
print("1. Приседания")
print("2. Отжимания")
print("3. Выпады")
print("4. Ягодичный мостик")
choice = input("Введите номер: ")

if choice == '1':
    exercise = Squat(); ex_name = "Приседания"
elif choice == '2':
    exercise = PushUp(); ex_name = "Отжимания"
elif choice == '3':
    exercise = Lunge(); ex_name = "Выпады"
elif choice == '4':
    exercise = GluteBridge(); ex_name = "Ягодичный мостик"
else:
    exit()

# ==========================================
# 3. НАСТРОЙКА
# ==========================================
active_points = [0, 7, 8, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
smoothed_landmarks = {}
alpha = 0.6

cap = cv2.VideoCapture(0)
last_speak_time = 0

# Переменные для таймера
workout_started = False
start_time = 0
countdown_duration = 3 # Секунды до старта

with PoseLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        frame_timestamp_ms = int(time.time() * 1000)

        result = landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        
        # ==========================================
        # БЛОК ТАЙМЕРА
        # ==========================================
        if not workout_started:
            if start_time == 0:
                start_time = time.time()
                # Можно добавить голосовое: speak("Приготовьтесь")
            
            elapsed = time.time() - start_time
            remaining = int(countdown_duration - elapsed) + 1
            
            if remaining > 0:
                # Выводим большие цифры по центру
                h, w, _ = frame.shape
                text = str(remaining)
                font_scale = 5
                thickness = 10
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                text_x = (w - text_size[0]) // 2
                text_y = (h + text_size[1]) // 2
                
                cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), thickness)
                cv2.putText(frame, "Приготовьтесь", (w // 2 - 100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            else:
                workout_started = True # Таймер закончился, включаем логику

        # ==========================================
        # ОСНОВНАЯ ЛОГИКА (Работает только после таймера)
        # ==========================================
        if workout_started and result.pose_landmarks:
            raw_landmarks = result.pose_landmarks[0]
            
            class SmoothLandmark:
                def __init__(self, x, y): self.x, self.y = x, y
            
            smoothed_list = [None] * 33

            for i in active_points:
                raw_x = raw_landmarks[i].x
                raw_y = raw_landmarks[i].y
                
                if i in smoothed_landmarks:
                    prev_x, prev_y = smoothed_landmarks[i]
                    new_x = prev_x * alpha + raw_x * (1 - alpha)
                    new_y = prev_y * alpha + raw_y * (1 - alpha)
                else:
                    new_x, new_y = raw_x, raw_y
                
                smoothed_landmarks[i] = (new_x, new_y)
                smoothed_list[i] = SmoothLandmark(new_x, new_y)

            # Передаем в логику
            angle = exercise.process(smoothed_list)

            # Отрисовка скелета
            def draw_line(idx1, idx2):
                if smoothed_list[idx1] and smoothed_list[idx2]:
                    p1 = (int(smoothed_list[idx1].x * frame.shape[1]), int(smoothed_list[idx1].y * frame.shape[0]))
                    p2 = (int(smoothed_list[idx2].x * frame.shape[1]), int(smoothed_list[idx2].y * frame.shape[0]))
                    cv2.line(frame, p1, p2, (255, 0, 255), 2)
                    cv2.circle(frame, p1, 4, (0, 255, 0), -1)
                    cv2.circle(frame, p2, 4, (0, 255, 0), -1)

            def get_center(idx1, idx2):
                if smoothed_list[idx1] and smoothed_list[idx2]:
                    return (int((smoothed_list[idx1].x + smoothed_list[idx2].x) / 2 * frame.shape[1]), int((smoothed_list[idx1].y + smoothed_list[idx2].y) / 2 * frame.shape[0]))
                return None

            # Руки
            draw_line(11, 13); draw_line(13, 15)
            draw_line(12, 14); draw_line(14, 16)
            # Ноги
            draw_line(23, 25); draw_line(25, 27)
            draw_line(24, 26); draw_line(26, 28)
            # Тело
            draw_line(11, 12)
            draw_line(11, 23); draw_line(12, 24)
            draw_line(23, 24)

            # Позвоночник и шея
            neck = get_center(11, 12)
            pelvis = get_center(23, 24)
            
            if neck and pelvis:
                cv2.line(frame, neck, pelvis, (255, 0, 255), 2) 
                nose_x = int(smoothed_list[0].x * frame.shape[1])
                nose_y = int(smoothed_list[0].y * frame.shape[0])
                cv2.line(frame, neck, (nose_x, nose_y), (255, 0, 255), 2)

                # Голова (овал)
                if smoothed_list[7] and smoothed_list[8]:
                    ear_l = (int(smoothed_list[7].x * frame.shape[1]), int(smoothed_list[7].y * frame.shape[0]))
                    ear_r = (int(smoothed_list[8].x * frame.shape[1]), int(smoothed_list[8].y * frame.shape[0]))
                    center_x = (ear_l[0] + ear_r[0]) // 2
                    center_y = (ear_l[1] + ear_r[1]) // 2
                    width = abs(ear_l[0] - ear_r[0])
                    height = int(width * 1.4)
                    angle_head = np.degrees(np.arctan2(ear_r[1] - ear_l[1], ear_r[0] - ear_l[0]))
                    cv2.ellipse(frame, (center_x, center_y), (width // 2 + 15, height // 2 + 15), angle_head, 0, 360, (0, 255, 255), 2)
                    cv2.circle(frame, (nose_x, nose_y), 4, (0, 255, 0), -1)

            # Ошибки
            if exercise.current_errors:
                y_offset = 30
                for err in exercise.current_errors:
                    cv2.putText(frame, err, (10, frame.shape[0] - y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    y_offset += 30
                
                current_time = time.time()
                if current_time - last_speak_time > 2.0:
                    error_to_speak = exercise.current_errors[0]
                    feedback = get_feedback(ex_name, error_to_speak)
                    speak(feedback)
                    last_speak_time = current_time

        # Интерфейс (Счетчик)
        if workout_started:
            cv2.rectangle(frame, (0, 0), (350, 80), (0, 0, 0), -1)
            cv2.putText(frame, f"{ex_name}: {exercise.counter}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        cv2.imshow('CoolCoach AI', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

print("\n--- ТРЕНИРОВКА ЗАВЕРШЕНА ---")
print(f"Упражнение: {ex_name}")
print(f"Повторений: {exercise.counter}")
print(f"Зафиксировано ошибок: {exercise.errors}")