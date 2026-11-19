from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "mysql+aiomysql://user:password@localhost:3306/coolcoach" 
    secret_key: str = "change-me"   # секретный ключ для шифрования токенов
    algorithm: str = "HS256"   # алгоритм шифрования токенов
    access_token_expire_minutes: int = 60 * 24 * 30 # 30 дней жизни токена
    smtp_host: str = "smtp.yandex.ru"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    app_base_url: str = "http://127.0.0.1:8000"


settings = Settings()
