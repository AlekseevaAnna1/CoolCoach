from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Хеширует пароль. Принимает строку и возвращает хеш.
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Проверяет пароль. Принимает строку и возвращает bool.
def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


# Создаёт токен доступа. Принимает строку и возвращает токен.
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes) # Устанавливаем время истечения токена.
    payload = {"sub": subject, "exp": expire} # Создаём payload для токена.
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm) # Кодируем payload в токен и возвращаем его.
