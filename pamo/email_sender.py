from django.core.mail import send_mail
from pamo.constants import EMAIL_HOST_USER


class EmailSender:
    """
    Clase para enviar correos electrónicos con contenido HTML.
    """

    def __init__(self, from_email=EMAIL_HOST_USER):
        """
        Inicializa el remitente de correos.
        :param from_email: Correo electrónico del remitente. Si no se proporciona, usa el valor por defecto.
        """
        self.from_email = from_email  # Cambia esto según tu configuración

    def send_html_email(self, subject, html_message, recipient_list):
        """
        Envía un correo electrónico con contenido HTML.
        :param subject: Asunto del correo.
        :param html_message: Contenido HTML del mensaje.
        :param recipient_list: Lista de destinatarios (lista de strings).
        """
        send_mail(
            subject,
            "",  # Mensaje de texto plano vacío, ya que usamos HTML
            self.from_email,
            recipient_list,
            html_message=html_message,
        )
