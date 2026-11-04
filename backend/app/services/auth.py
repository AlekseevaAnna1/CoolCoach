import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import PasswordResetConfirm, PasswordResetRequest, Token, UserCreate, UserLogin, UserUpdate
from app.services.security import (
    create_access_token,
    hash_password,
    read_access_token_subject,
    verify_password,
)

bearer_scheme = HTTPBearer()
PASSWORD_RESET_EXPIRE_MINUTES = 30


# Регистрация нового пользователя. Принимает UserCreate и возвращает User.
async def register_user(db: AsyncSession, data: UserCreate) -> User:
    # Проверяем, существует ли пользователь с таким email.
    existing_user = await db.scalar(select(User).where(User.email == data.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Создаём нового пользователя.
    user = User(
        email=data.email,
        password_hash=hash_password(data.password), # Хешируем пароль.
        name=data.name,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None), # Устанавливаем время создания пользователя.
    )
    db.add(user) # Добавляем пользователя в базу данных.
    await db.commit() # Сохраняем пользователя в базу данных.
    await db.refresh(user) # Обновляем пользователя в базе данных.
    return user


# Вход пользователя. Принимает UserLogin и возвращает Token.
async def login_user(db: AsyncSession, data: UserLogin) -> Token:
    user = await db.scalar(select(User).where(User.email == data.email))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    return Token(access_token=create_access_token(str(user.user_id)))


# Возвращает пользователя по токену из заголовка Authorization.
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    subject = read_access_token_subject(credentials.credentials)
    user = None
    if subject is not None and subject.isdigit():
        user = await db.get(User, int(subject))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return user


# Обновляет имя и email текущего пользователя.
async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    if data.email is not None and data.email != user.email:
        existing_user = await db.scalar(select(User).where(User.email == data.email))
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user.email = data.email
    if data.name is not None:
        user.name = data.name
    await db.commit()
    await db.refresh(user)
    return user


# Сохраняет токен восстановления пароля. Письмо пока не отправляется.
async def request_password_reset(db: AsyncSession, data: PasswordResetRequest) -> None:
    user = await db.scalar(select(User).where(User.email == data.email))
    if user is None:
        return
    user.reset_token = secrets.token_urlsafe(32)
    user.reset_token_expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
        minutes=PASSWORD_RESET_EXPIRE_MINUTES
    )
    await db.commit()


# Ставит новый пароль по токену из письма и очищает токен.
async def confirm_password_reset(db: AsyncSession, data: PasswordResetConfirm) -> None:
    user = await db.scalar(select(User).where(User.reset_token == data.token))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if user is None or user.reset_token_expiry is None or user.reset_token_expiry < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    user.password_hash = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    await db.commit()
