from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
    UserUpdate,
)
from app.services.auth import (
    confirm_password_reset,
    get_current_user,
    login_user,
    register_user,
    request_password_reset,
    update_user,
)

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


# Профиль текущего пользователя. Требует токен доступа.
@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


# Изменение имени и email. Требует токен доступа и возвращает UserRead.
@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserRead:
    user = await update_user(db, current_user, payload)
    return UserRead.model_validate(user)


# Запрос восстановления пароля. Ответ одинаковый, даже если email не найден.
@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await request_password_reset(db, payload)
    return {"detail": "If the email is registered, password reset instructions will be sent"}


# Установка нового пароля по токену из письма.
@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset_confirm(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> None:
    await confirm_password_reset(db, payload)
