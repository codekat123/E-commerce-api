from django.db import models
from user_profile.models import CustomerProfile,MerchantProfile
from product.models import Product
import secrets
from django.core.validators import MinValueValidator , MaxValueValidator
from django.utils import timezone

class Referral(models.Model):
    referrer = models.ForeignKey(CustomerProfile, related_name='referrals_sent', on_delete=models.CASCADE)
    referred = models.ForeignKey(CustomerProfile, related_name='referrals_received', null=True, blank=True, on_delete=models.SET_NULL)
    referral_code = models.CharField(max_length=20, unique=True)
    reward_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            while True:
                code = secrets.token_hex(4)
                if not Referral.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

class Coupon(models.Model):
    merchant = models.ForeignKey(MerchantProfile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(max_length=8, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    active = models.BooleanField(default=True)


    def is_valid(self):
        now = timezone.now()
        return (
            self.active
            and self.valid_from <= now <= self.valid_to
            and self.times_used < self.usage_limit
        )
