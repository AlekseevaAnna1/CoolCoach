from gtts import gTTS
import pygame
import io
import threading
import os

# Инициализируем микшер pygame для проигрывания звука
pygame.mixer.init()

def _speak_worker(text):
    try:
        # Генерируем аудио через Google TTS (язык русский)
        tts = gTTS(text=text, lang='ru')
        
        # Сохраняем во временный файл в памяти
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Загружаем и играем
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        
        # Ждем, пока музыка доиграет
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    except Exception as e:
        print(f"Ошибка озвучки: {e}")

def speak(text):
    if not text:
        return
    # Запускаем в отдельном потоке, чтобы видео не зависало
    thread = threading.Thread(target=_speak_worker, args=(text,))
    thread.daemon = True
    thread.start()