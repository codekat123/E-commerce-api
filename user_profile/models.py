from django.db import models
from django.contrib.auth import get_user_model
import pycountry

User = get_user_model()

def get_country_choices():
    return [(country.alpha_2, country.name) for country in pycountry.countries]

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    country = models.CharField(choices=get_country_choices(), max_length=50)
    phone_number = models.CharField(max_length=50)
    location = models.TextField(max_length=500)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class MerchantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='merchant_profile')
    business_name = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    country = models.CharField(choices=get_country_choices(), max_length=50)
    business_address = models.TextField(max_length=500)
    phone_number = models.CharField(max_length=50)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='merchants/logos/', blank=True, null=True)
    verified = models.BooleanField(default=False)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.business_name

