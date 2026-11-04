from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# Описывает JSON, который клиент отправляет серверу при регистрации.
class UserCreate(BaseModel):
    email: EmailStr = Field(max_length=100)
    password: str = Field(min_length=8, max_length=72)
    name: str | None = Field(default=None, max_length=45)


# Описывает JSON, который клиент отправляет серверу при входе в систему.
class UserLogin(BaseModel):
    email: EmailStr = Field(max_length=100)
    password: str = Field(min_length=8, max_length=72)


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


# Описывает JSON для изменения имени и email уже вошедшего пользователя.
class UserUpdate(BaseModel):
    email: EmailStr | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=45)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserUpdate":
        if self.email is None and self.name is None:
            raise ValueError("Укажите имя или email")
        return self


# Описывает JSON запроса ссылки для восстановления пароля.
class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(max_length=100)


# Описывает JSON установки нового пароля по токену из письма.
class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=72)
