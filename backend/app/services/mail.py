import ssl
from email.message import EmailMessage

import aiosmtplib
import truststore
from fastapi import HTTPException, status

from app.config import settings


# Отправляет токен восстановления на почту пользователя.
async def send_password_reset_email(recipient: str, token: str) -> None:
    if not settings.smtp_user or not settings.smtp_password or not settings.smtp_from:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is not configured",
        )

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = "Восстановление пароля CoolCoach"
    message.set_content(
        "Чтобы задать новый пароль, отправьте этот токен на "
        f"{settings.app_base_url}/auth/password-reset/confirm\n\n"
        f"Токен: {token}\n"
        "Он действует 30 минут. Если вы не запрашивали сброс, проигнорируйте письмо."
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=settings.smtp_port == 465,
            start_tls=settings.smtp_port != 465,
            tls_context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        )
    except aiosmtplib.SMTPException as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send password reset email: {error}",
        ) from error
