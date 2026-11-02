from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Описывает JSON, который клиент отправляет серверу при регистрации.
class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=100)
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=45)


# Описывает JSON, который клиент отправляет серверу при входе в систему.
class UserLogin(BaseModel):
    email: EmailStr = Field(max_length=100)
    password: str


# Описывает JSON, который сервер отдаёт клиенту после регистрации.
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: EmailStr
    name: str | None
    created_at: datetime


# Описывает JSON, который сервер отдаёт клиенту после входа в систему.
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
