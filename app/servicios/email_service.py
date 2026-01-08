"""
Servicio de Email - TutorIA

Soporta múltiples proveedores de email:
1. SMTP (Gmail, Outlook, cualquier servidor SMTP)
2. SendGrid (API)
3. Modo desarrollo (imprime en consola)

Configuración vía variables de entorno en .env
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from pathlib import Path

from app import settings
from app.logs.logger import logger


class EmailService:
    """
    Servicio centralizado para envío de emails.

    Características:
    - Múltiples proveedores (SMTP, SendGrid)
    - Plantillas HTML
    - Modo desarrollo (no envía, solo imprime)
    - Logging completo
    - Manejo de errores robusto
    """

    def __init__(self):
        self.email_provider = getattr(settings, 'EMAIL_PROVIDER', 'smtp').lower()
        self.email_from = getattr(settings, 'EMAIL_FROM', 'noreply@tutoria.com')
        self.frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')

        # Configuración SMTP
        self.smtp_host = getattr(settings, 'SMTP_HOST', None)
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.smtp_use_tls = getattr(settings, 'SMTP_USE_TLS', True)

        # Configuración SendGrid
        self.sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None)

    def _load_template(self, template_name: str) -> str:
        """
        Carga una plantilla HTML desde app/templates/

        Args:
            template_name: Nombre del archivo de plantilla (ej: 'email_reset_password.html')

        Returns:
            str: Contenido HTML de la plantilla
        """
        template_path = Path(__file__).parent.parent / 'templates' / template_name

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"⚠️ Plantilla {template_name} no encontrada, usando HTML básico")
            return "<html><body>{content}</body></html>"

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía email usando SMTP.

        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML
            text_content: Contenido texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False si hubo error
        """
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.error("❌ Configuración SMTP incompleta. Verifica .env")
            return False

        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = to_email

            # Agregar contenido texto plano (fallback)
            if text_content:
                part_text = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part_text)

            # Agregar contenido HTML
            part_html = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part_html)

            # Conectar y enviar
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"📧 Email SMTP enviado exitosamente a {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error al enviar email SMTP a {to_email}: {str(e)}")
            return False

    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía email usando SendGrid API.

        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML
            text_content: Contenido texto plano (opcional)

        Returns:
            bool: True si se envió correctamente, False si hubo error
        """
        if not self.sendgrid_api_key:
            logger.error("❌ SENDGRID_API_KEY no configurada. Verifica .env")
            return False

        try:
            # Importar SendGrid (solo si se necesita)
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content

            # Crear mensaje
            message = Mail(
                from_email=self.email_from,
                to_emails=to_email,
                subject=subject
            )

            # Agregar contenido
            if text_content:
                message.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
            else:
                message.content = Content("text/html", html_content)

            # Enviar
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)

            logger.info(
                f"📧 Email SendGrid enviado exitosamente a {to_email}. "
                f"Status: {response.status_code}"
            )
            return True

        except ImportError:
            logger.error("❌ Módulo sendgrid no instalado. Ejecuta: pip install sendgrid")
            return False
        except Exception as e:
            logger.error(f"❌ Error al enviar email SendGrid a {to_email}: {str(e)}")
            return False

    def _send_dev_mode(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ):
        """
        Modo desarrollo: Imprime el email en la consola en lugar de enviarlo.

        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML
        """
        logger.info("=" * 80)
        logger.info("📧 [MODO DESARROLLO] Email NO enviado (solo impreso en consola)")
        logger.info(f"Para: {to_email}")
        logger.info(f"Asunto: {subject}")
        logger.info(f"De: {self.email_from}")
        logger.info("-" * 80)
        logger.info("Contenido HTML:")
        logger.info(html_content[:500] + "..." if len(html_content) > 500 else html_content)
        logger.info("=" * 80)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envía un email usando el proveedor configurado.

        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML
            text_content: Contenido texto plano (opcional)

        Returns:
            bool: True si se envió (o modo dev), False si hubo error
        """
        # Modo desarrollo: solo imprimir
        if self.email_provider == 'dev' or self.email_provider == 'development':
            self._send_dev_mode(to_email, subject, html_content)
            return True

        # SMTP
        elif self.email_provider == 'smtp':
            return self._send_via_smtp(to_email, subject, html_content, text_content)

        # SendGrid
        elif self.email_provider == 'sendgrid':
            return self._send_via_sendgrid(to_email, subject, html_content, text_content)

        else:
            logger.error(f"❌ Proveedor de email desconocido: {self.email_provider}")
            return False

    def send_reset_password_email(
        self,
        to_email: str,
        usuario_nombre: str,
        reset_token: str
    ) -> bool:
        """
        Envía email de reset de contraseña.

        Args:
            to_email: Email del destinatario
            usuario_nombre: Nombre del usuario
            reset_token: Token de reset

        Returns:
            bool: True si se envió correctamente
        """
        # Cargar plantilla
        template = self._load_template('email_reset_password.html')

        # URL completa para resetear
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"

        # Reemplazar variables en la plantilla
        html_content = template.replace('{{USUARIO_NOMBRE}}', usuario_nombre)
        html_content = html_content.replace('{{RESET_URL}}', reset_url)
        html_content = html_content.replace('{{TOKEN}}', reset_token)
        html_content = html_content.replace('{{FRONTEND_URL}}', self.frontend_url)

        # Contenido texto plano (fallback)
        text_content = f"""
Hola {usuario_nombre},

Recibimos una solicitud para resetear tu contraseña en TutorIA.

Si fuiste tú, haz clic en el siguiente enlace para crear una nueva contraseña:
{reset_url}

O copia y pega este token en la aplicación:
{reset_token}

Este enlace expira en 1 hora.

Si no solicitaste este cambio, puedes ignorar este email de forma segura.

Saludos,
Equipo TutorIA
        """.strip()

        # Enviar
        subject = "Resetear Contraseña - TutorIA"
        return self.send_email(to_email, subject, html_content, text_content)


# Instancia global del servicio
email_service = EmailService()
