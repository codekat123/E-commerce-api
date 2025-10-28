from celery import shared_task
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(self ,subject, html_content, recipient_list):
    """
    Sends email asynchronously via Brevo API.
    Retries up to 3 times if sending fails.
    """
    try:
        # Prepare request payload
        payload = {
            "sender": {
                "name": "ShopAI",
                "email": settings.DEFAULT_FROM_EMAIL,  # ✅ make sure this is set
            },
            "to": [{"email": email} for email in recipient_list],
            "subject": subject,
            "htmlContent": html_content,
        }

        # Send POST request to Brevo API
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": settings.BREVO_API_KEY,
                "content-type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        # Check for success
        if response.status_code not in (200, 201, 202):
            raise Exception(f"Brevo API error: {response.status_code} {response.text}")

        logger.info(f"✅ Email sent successfully to {recipient_list}")
        return f"Email sent successfully to {recipient_list}"

    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        raise self.retry(exc=e)
