from django.db import models
import random
import string
from django.utils import timezone
from product.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()


def generate_order_id(length=8):
     characters = string.ascii_letters + string.digits
     return ''.join(random.choices(characters,k=length))


class Order(models.Model):
     user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='order')
     order_id = models.CharField(max_length = 8 , default = generate_order_id,unique=True)
     first_name = models.CharField(max_length = 30)
     last_name = models.CharField(max_length = 30)
     city = models.CharField(max_length = 30)
     address = models.CharField(max_length = 200)
     email = models.EmailField()
     created_at = models.DateTimeField(default=timezone.now)
     update_at = models.DateTimeField(auto_now_add = True)
     paid = models.BooleanField(default=False)
     postal_code = models.PositiveIntegerField()

     class Meta:
          ordering = ['-created_at']
          indexes = [
               models.Index(fields=['created_at'])
          ]
     
     def __str__(self):
          return f"order_id => {self.order_id}"
     
     def save(self,*args,**kwargs):
          if not self.order_id:
               unique_id = generate_order_id()
               while Order.objects.filter(order_id = unique_id).exists():
                    unique_id = generate_order_id()
               self.order_id = unique_id
          super().save(*args,**kwargs)

     def get_products(self):
         return [item.product for item in self.order_item.all()]
     
     def get_status(self):
         latest_status = self.order_status.order_by('-timestamp').first()
         return latest_status.status if latest_status else None





class OrderItem(models.Model):
     order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='order_item')
     product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='order_item')
     price = models.DecimalField(max_digits=6,decimal_places=2)
     quantity = models.PositiveIntegerField(default=1)
     created_at = models.DateField(auto_now_add=True)


class OrderStatus(models.Model):
     class Status(models.TextChoices):
          CANCELLED = 'Cancelled','cancelled'
          Pending = 'Pending','pending'
          SHIPPED = 'Shipped','shipped'
          DELIVERED = 'Delivered','delivered'

     order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='order_status')
     status = models.CharField(max_length=30,choices=Status.choices,default=Status.Pending)
     timestamp = models.DateTimeField(auto_now_add=True)
     

class OrderPayment(models.Model):
     order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='order_paytment')
     image = models.ImageField()
     phone_number = models.CharField(max_length=30)

     
