from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order,OrderStatus
from .tasks import send_invoice_email
@receiver(post_save,sender=Order)
def order_status(sender, instance, created, **kwargs):
     if created:
          OrderStatus.objects.create(order=instance)


