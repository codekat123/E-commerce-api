from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject, message, recipient_list):
    """
    Sends an email asynchronously using Celery.
    Retries up to 3 times if sending fails.
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        return f"Email sent successfully to {recipient_list}"
    except Exception as e:
        self.retry(exc=e, countdown=10)
        return f"Email sending failed: {e}"
