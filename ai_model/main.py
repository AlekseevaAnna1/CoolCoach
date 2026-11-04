import cv2
import mediapipe as mp
import urllib.request
import os
import time

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
# 3. ЗАПУСК
# ==========================================
cap = cv2.VideoCapture(0)
last_speak_time = 0
last_error_for_llm = ""

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
        
        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            
            # Обработка упражнения
            angle = exercise.process(landmarks)

            # Рисуем скелет
            for lm in landmarks:
                x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
            
            connections = mp.tasks.vision.PoseLandmarksConnections.POSE_LANDMARKS
            for connection in connections:
                start_point = (int(landmarks[connection.start].x * frame.shape[1]), int(landmarks[connection.start].y * frame.shape[0]))
                end_point = (int(landmarks[connection.end].x * frame.shape[1]), int(landmarks[connection.end].y * frame.shape[0]))
                cv2.line(frame, start_point, end_point, (255, 0, 255), 2)

            # === ОБРАБОТКА ОШИБОК И ГОЛОС ===
            if exercise.current_errors:
                # 1. Выводим на экран все ошибки
                y_offset = 30
                for err in exercise.current_errors:
                    cv2.putText(frame, err, (10, frame.shape[0] - y_offset), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    y_offset += 30
                
                # 2. Озвучиваем
                current_time = time.time()
                # Если прошло больше 2 секунд с последней озвучки
                if current_time - last_speak_time > 2.0:
                    # Берем первую ошибку из списка для озвучки
                    error_to_speak = exercise.current_errors[0]
                    
                    # Если ошибка изменилась, или просто прошло время — генерируем текст
                    feedback = get_feedback(ex_name, error_to_speak)
                    speak(feedback)
                    
                    last_speak_time = current_time

            # === РИСУЕМ СКЕЛЕТ ===
            # 1. Точки
            for lm in landmarks:
                x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
            
            # 2. Линии (соединяем основные суставы)
            connections = mp.tasks.vision.PoseLandmarksConnections.POSE_LANDMARKS
            for connection in connections:
                start_point = (int(landmarks[connection.start].x * frame.shape[1]), int(landmarks[connection.start].y * frame.shape[0]))
                end_point = (int(landmarks[connection.end].x * frame.shape[1]), int(landmarks[connection.end].y * frame.shape[0]))
                cv2.line(frame, start_point, end_point, (255, 0, 255), 2)

        # Интерфейс
        cv2.rectangle(frame, (0, 0), (350, 80), (0, 0, 0), -1)
        cv2.putText(frame, f"{ex_name}: {exercise.counter}", (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        cv2.imshow('CoolCoach AI', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

print("\n--- ТРЕНИРОВКА ЗАВЕРШЕНА ---")
print(f"Упражнение: {ex_name}")
print(f"Повторений: {exercise.counter}")
print(f"Зафиксировано ошибок: {exercise.errors}")