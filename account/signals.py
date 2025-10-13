from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from user_profile.models import CustomerProfile, MerchantProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.roles == "Merchant":
            MerchantProfile.objects.create(user=instance)
        else:
            CustomerProfile.objects.create(user=instance)
