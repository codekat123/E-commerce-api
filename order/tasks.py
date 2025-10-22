from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from .models import Order
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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
    try:
        order = get_object_or_404(Order, order_id=order_id)

        # Create a PDF using ReportLab
        pdf_buffer = BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=A4)
        p.setFont("Helvetica", 12)

        p.drawString(100, 800, f"Invoice for Order #{order.order_id}")
        p.drawString(100, 780, f"Customer: {order.first_name} {order.last_name}")
        p.drawString(100, 760, f"Email: {order.user.email}")

        p.drawString(100, 700, "Thank you for shopping with us!")
        p.showPage()
        p.save()

        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.getvalue()

        subject = f"📦 Your Order Invoice — {order.order_id}"
        html_content = render_to_string("emails/invoice_email.html", {"order": order})

        attachments = [
            {
                "name": f"invoice_{order.order_id}.pdf",
                "content": pdf_bytes.decode("latin1"),
                "type": "application/pdf",
            }
        ]

        send_via_brevo(subject, html_content, order.user.email, attachments)
        return f"Invoice email sent to {order.user.email}"

    except Exception as e:
        self.retry(exc=e, countdown=10)
        return f"Invoice email failed: {e}"
