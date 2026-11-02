from pydantic import BaseModel, ConfigDict, Field


class SessionErrorCreate(BaseModel): // описывает JSON, который клиент отправляет серверу при создании ошибки сессии
    error_type: str = Field(max_length=45)
    error_count: int = Field(ge=0)
    first_occurred_sec: int = Field(ge=0)


class SessionErrorRead(BaseModel): // описывает JSON, который сервер отдаёт клиенту после получения ошибки сессии
    model_config = ConfigDict(from_attributes=True)

    error_id: int
    session_id: int
    error_type: str
    error_count: int
    first_occurred_sec: int
