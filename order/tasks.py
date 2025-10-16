from celery import shared_task
from django.core.mail import send_mail , EmailMessage
from django.conf import settings
from .models import Order
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

@shared_task(bind=True,max_retries=3)
def send_mails(self,order_id):
     order = Order.objects.select_related('user').get(order_id=order_id)
     subject = "!Order confirmed"
     message = (
          f"Hello{order.first_name}\n\n"
          "your order has beeen confirmed successfully\n"
          f"your order id is : {order.order_id}"
     )
     try:
          send_mail(
               subject,
               message,
               settings.DEFAULT_FROM_EMAIL,
               [order.user.email],
               False
          )
          return f"email sent successfully to {order.user.email}"
     except Exception as e :
          self.retry(exc=e,countdown=10)
          return f"Email sending failed:{e}"


@shared_task
def send_invoice(order_id):
     import weasyprint
     from io import BytesIO
     order = Order.objects.get(order_id=order_id)
     subject = f"your order is arrived - invoice - {order.order_id}"
     message = f"Hello {order.first_name} \n please find attached the invoice for your recent purchase"
     from_email = settings.DEFAULT_FROM_EMAIL
     to_email = [order.email]
     html = render_to_string('order/pdf.html',{'order':order})
     out = BytesIO()
     weasyprint.HTML(string=html).write_pdf(out)

     email = EmailMessage(
          subject = subject,
          from_email = from_email,
          body=message,
          to = to_email,
     )
     email.attach(f'order_{order.order_id}.pdf',out.getvalue(),'application/pdf')
     email.send()
     return True