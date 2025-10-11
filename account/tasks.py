from celery import shared_task
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


@shared_task
def send_validation_email(domain, protocal, uid, token, name, user_email):
    subject = 'Please activate your email'
    activation_link = f"{protocal}://{domain}{reverse('account:verify_email', args=[token, uid])}"
    context = {
        'name': name,
        'link': activation_link,
    }
    message = render_to_string('email_actvation.html', context)

    try:
        mail = EmailMultiAlternatives(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email]
        )
        mail.attach_alternative(message, 'text/html')
        mail.send(fail_silently=False)  
        print(f"✅ Email sent successfully to {user_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {user_email}: {e}")
        raise e   