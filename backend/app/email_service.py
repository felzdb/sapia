import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def send_confirmation_email(recipient: str, token: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM")
    app_base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")

    if not all([smtp_host, smtp_user, smtp_password, smtp_from]):
        raise RuntimeError("Configuração de e-mail incompleta.")

    confirmation_url = f"{app_base_url}/auth/confirm?token={token}"

    message = EmailMessage()
    message["Subject"] = "Confirme seu cadastro no SAPIA"
    message["From"] = smtp_from
    message["To"] = recipient
    message.set_content(
        "Olá!\n\n"
        "Para confirmar seu cadastro no SAPIA, acesse o link abaixo:\n\n"
        f"{confirmation_url}\n\n"
        "Se você não realizou este cadastro, ignore esta mensagem."
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)
        