from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin
from app.services.security import create_access_token, hash_password, verify_password


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
