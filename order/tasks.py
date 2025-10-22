from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from .models import Order
import requests
import weasyprint
from io import BytesIO

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_via_brevo(subject, html_content, to_email, attachments=None):
    """Helper to send an email through Brevo’s API."""
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    data = {
        "sender": {"name": "Shop", "email": settings.DEFAULT_FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }

    if attachments:
        data["attachment"] = attachments

    response = requests.post(BREVO_API_URL, headers=headers, json=data, timeout=10)
    if response.status_code not in (200, 201, 202):
        raise Exception(f"Brevo API error: {response.status_code} - {response.text}")

    return response.json()


@shared_task(bind=True, max_retries=3)
def send_order_confirmation(self, order_id):
    """Send a confirmation email asynchronously."""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        subject = "🛒 Order Confirmed!"
        html_content = render_to_string("emails/order_confirmation.html", {"order": order})

        send_via_brevo(subject, html_content, order.user.email)

        return f"Email sent successfully to {order.user.email}"

    except Exception as e:
        self.retry(exc=e, countdown=10)
        return f"Email sending failed: {e}"


@shared_task(bind=True, max_retries=3)
def send_invoice_email(self, order_id):
    """Send a PDF invoice as an attachment via Brevo."""
    try:
        order = get_object_or_404(Order, order_id=order_id)

        # Render invoice HTML → PDF
        html = render_to_string("order/pdf.html", {"order": order})
        pdf_file = BytesIO()
        weasyprint.HTML(string=html).write_pdf(pdf_file)

        subject = f"📦 Your Order Invoice — {order.order_id}"
        html_content = render_to_string("emails/invoice_email.html", {"order": order})

        attachments = [
            {
                "name": f"invoice_{order.order_id}.pdf",
                "content": pdf_file.getvalue().decode("latin1"),
                "type": "application/pdf",
            }
        ]

        send_via_brevo(subject, html_content, order.user.email, attachments)
        return f"Invoice email sent to {order.user.email}"

    except Exception as e:
        self.retry(exc=e, countdown=10)
        return f"Invoice email failed: {e}"
