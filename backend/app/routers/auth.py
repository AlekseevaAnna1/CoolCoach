from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import Token, UserCreate, UserLogin, UserRead
from app.services.auth import login_user, register_user

router = APIRouter()


# Регистрация нового пользователя. Принимает UserCreate и возвращает UserRead.
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    user = await register_user(db, payload)
    return UserRead.model_validate(user)


# Вход пользователя. Принимает UserLogin и возвращает Token.
@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    return await login_user(db, payload)
