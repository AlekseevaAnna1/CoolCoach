from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel): // описывает JSON, который клиент отправляет серверу при регистрации
    email: EmailStr = Field(max_length=100)
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=45)


class UserLogin(BaseModel): // описывает JSON, который клиент отправляет серверу при входе в систему
    email: EmailStr = Field(max_length=100)
    password: str


class UserRead(BaseModel): // описывает JSON, который сервер отдаёт клиенту после регистрации
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: EmailStr
    name: str | None
    created_at: datetime


class Token(BaseModel): // описывает JSON, который сервер отдаёт клиенту после входа в систему
    access_token: str
    token_type: str = "bearer"
