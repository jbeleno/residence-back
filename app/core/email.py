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
        "login": "Código de inicio de sesión",
        "reset_password": "Restablecer contraseña",
        "verify_email": "Verifica tu cuenta",
        "change_email": "Confirma tu nuevo correo",
    }
    intros = {
        "login": "Recibimos una solicitud para iniciar sesión en tu cuenta. Usa el siguiente código para continuar:",
        "reset_password": "Recibimos una solicitud para restablecer la contraseña de tu cuenta. Usa el siguiente código para continuar:",
        "verify_email": "Gracias por registrarte. Usa el siguiente código para verificar tu correo y activar tu cuenta:",
        "change_email": "Solicitaste cambiar tu correo electrónico. Usa el siguiente código para confirmar tu nuevo correo:",
    }
    title = titles.get(pin_type, "Código de verificación")
    intro = intros.get(
        pin_type,
        "Usa el siguiente código de verificación para continuar:",
    )

    # Brand palette inspired by Resi (chatbot avatar):
    # - primary orange   #F26B1F  (CTAs, highlights)
    # - cream background #FAF6F1  (page bg)
    # - card background  #FFFFFF
    # - navy text        #1B2845  (titles, code)
    # - muted text       #5C6477
    # - subtle border    #ECE6DC

    pin_spaced = " ".join(pin)

    return f"""\
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin:0; padding:0; background-color:#FAF6F1; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color:#1B2845;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FAF6F1; padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px; background:#FFFFFF; border-radius:16px; border:1px solid #ECE6DC; overflow:hidden; box-shadow:0 4px 24px rgba(27,40,69,0.06);">
          <!-- Header con avatar Resi -->
          <tr>
            <td style="padding:32px 32px 16px 32px; text-align:left;">
              <table role="presentation" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <div style="width:44px; height:44px; background:#F26B1F; border-radius:50%; text-align:center; line-height:44px; color:#FFFFFF; font-size:22px; font-weight:bold; display:inline-block;">✦</div>
                  </td>
                  <td style="padding-left:12px; vertical-align:middle;">
                    <div style="font-size:14px; color:#5C6477; line-height:1; margin-bottom:4px;">Residence</div>
                    <div style="font-size:18px; font-weight:600; color:#1B2845; line-height:1;">Conjunto Los Pinos</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 32px;">
              <div style="height:1px; background:#ECE6DC;"></div>
            </td>
          </tr>

          <!-- Title -->
          <tr>
            <td style="padding:28px 32px 8px 32px;">
              <h1 style="margin:0; font-size:22px; font-weight:600; color:#1B2845; letter-spacing:-0.2px;">{title}</h1>
            </td>
          </tr>

          <!-- Greeting + intro -->
          <tr>
            <td style="padding:8px 32px 0 32px;">
              <p style="margin:0 0 12px 0; font-size:15px; color:#1B2845; line-height:1.5;">Hola <strong>{user_name}</strong>,</p>
              <p style="margin:0; font-size:15px; color:#5C6477; line-height:1.6;">{intro}</p>
            </td>
          </tr>

          <!-- PIN display -->
          <tr>
            <td style="padding:28px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="background:#FAF6F1; border:1px dashed #F26B1F; border-radius:12px; padding:24px 16px;">
                    <div style="font-size:12px; color:#5C6477; text-transform:uppercase; letter-spacing:2px; margin-bottom:12px; font-weight:600;">Tu código</div>
                    <div style="font-size:38px; font-weight:700; color:#1B2845; letter-spacing:10px; font-family: 'SF Mono', Menlo, Consolas, 'Courier New', monospace;">{pin_spaced}</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Expiry note -->
          <tr>
            <td style="padding:0 32px 12px 32px;">
              <p style="margin:0; font-size:14px; color:#5C6477; line-height:1.6;">
                Este código expira en <strong style="color:#1B2845;">{settings.PIN_EXPIRE_MINUTES} minutos</strong>.
                Por seguridad, no lo compartas con nadie.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 32px 32px 32px;">
              <div style="height:1px; background:#ECE6DC; margin-bottom:20px;"></div>
              <p style="margin:0; font-size:12px; color:#9AA0AC; line-height:1.6;">
                Si no solicitaste este código, puedes ignorar este mensaje. Tu cuenta sigue segura.
              </p>
              <p style="margin:12px 0 0 0; font-size:11px; color:#B7BDC7; line-height:1.5;">
                Este es un mensaje automático de <strong style="color:#5C6477;">Residence</strong> — por favor no respondas a este correo.
              </p>
            </td>
          </tr>
        </table>

        <!-- Bottom brand strip -->
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px; margin-top:16px;">
          <tr>
            <td align="center" style="font-size:11px; color:#B7BDC7; padding:0 16px;">
              © Residence · Plataforma de gestión de conjuntos residenciales
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
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
