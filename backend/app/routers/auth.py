from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.auth import register_user

router = APIRouter()


# Регистрация нового пользователя. Принимает UserCreate и возвращает UserRead.
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    user = await register_user(db, payload)
    return UserRead.model_validate(user)
