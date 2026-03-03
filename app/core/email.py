"""Email service – sends PIN codes via SMTP (async-compatible)."""

from __future__ import annotations

import random
import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def generate_pin(length: int = 6) -> str:
    """Generate a numeric PIN of the given length."""
    return "".join(random.choices(string.digits, k=length))


def _build_html(pin: str, pin_type: str, user_name: str) -> str:
    titles = {
        "login": "Código de verificación de inicio de sesión",
        "reset_password": "Código para restablecer contraseña",
        "verify_email": "Código de verificación de cuenta",
    }
    title = titles.get(pin_type, "Código de verificación")

    return f"""\
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 480px; margin: auto; background: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h2 style="color: #2c3e50; text-align: center;">{title}</h2>
            <p style="color: #555;">Hola <strong>{user_name}</strong>,</p>
            <p style="color: #555;">Tu código de verificación es:</p>
            <div style="text-align: center; margin: 25px 0;">
                <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #2c3e50; background: #ecf0f1; padding: 12px 24px; border-radius: 8px;">{pin}</span>
            </div>
            <p style="color: #888; font-size: 13px;">Este código expira en <strong>{settings.PIN_EXPIRE_MINUTES} minutos</strong>. No lo compartas con nadie.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #aaa; font-size: 11px; text-align: center;">Si no solicitaste este código, ignora este mensaje.</p>
        </div>
    </body>
    </html>"""


def send_pin_email(to_email: str, pin: str, pin_type: str, user_name: str) -> None:
    """Send a PIN code to the given email address via SMTP."""
    subject_map = {
        "login": "Tu código de inicio de sesión",
        "reset_password": "Restablecer contraseña",
        "verify_email": "Verifica tu cuenta",
    }

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{settings.APP_NAME} – {subject_map.get(pin_type, 'Código')}"
    msg["From"] = f"{settings.APP_NAME} <{settings.SMTP_FROM}>"
    msg["To"] = to_email

    html = _build_html(pin, pin_type, user_name)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        if settings.SMTP_TLS:
            server.starttls()
            server.ehlo()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
