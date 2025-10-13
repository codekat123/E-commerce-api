from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_activation_email(subject, message, recipient_email):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
    except Exception as e:
        # You can log this error properly later
        print(f"Failed to send email: {e}")

@shared_task
def send_reset_password_email(subject, message, recipient_email):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
    except Exception as e:
        print(f"Failed to send reset email: {e}")