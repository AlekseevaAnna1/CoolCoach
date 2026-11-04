import os
from openai import OpenAI
from dotenv import load_dotenv

# Загружаем переменные из файла .env
# Ищем файл .env в той же папке, где лежит llm_agent.py
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Берем ключ из .env. Если файла .env нет, ключ будет None
API_KEY = os.getenv("KODIK_API_KEY")

client = OpenAI(
    base_url="https://api.kodikrouter.ru/v1",
    api_key=API_KEY
)

_cache = {}

def get_feedback(exercise_name, error_text):
    if not error_text:
        return ""
    
    cache_key = f"{exercise_name}_{error_text}"
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты профессиональный фитнес-тренер. Дай короткую (до 10 слов), четкую и мотивирующую подсказку на русском языке."},
                {"role": "user", "content": f"Упражнение: {exercise_name}. Ошибка: {error_text}"}
            ],
            temperature=0.7,
            max_tokens=30
        )
        text = response.choices[0].message.content.strip()
        _cache[cache_key] = text
        return text
    except Exception as e:
        print(f"\n[!] Ошибка LLM (KodikRouter): {e}")
        return error_text # Если API упал, возвращаем сырой текст ошибки