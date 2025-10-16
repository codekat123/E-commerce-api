from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order,OrderStatus
from .tasks import send_mails, send_invoice
@receiver(post_save,sender=Order)
def order_status(sender, instance, created, **kwargs):
     if created:
          OrderStatus.objects.create(order=instance)
     else:
          latest_status = instance.order_status.last()
          if latest_status and latest_status.status == "Delivered":
               send_invoice(instance.order_id)

