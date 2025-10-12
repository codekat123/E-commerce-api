from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from .models import User

@receiver(post_save,sender=User)
def send_verification_email(sender,instance,created,**kwargs):
     pass