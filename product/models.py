from django.db import models
from user_profile.models import MerchantProfile,CustomerProfile
from django.utils.text import slugify
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name




class Product(models.Model):
    merchant = models.ForeignKey(MerchantProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    amount = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            count = 1
            # ensure uniqueness
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category})"


class ProductRating(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='rating')
    user = models.ForeignKey(CustomerProfile,on_delete=models.CASCADE,related_name='rate')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])  
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product") 

    def __str__(self):
        return f"{self.user.first_name} - {self.rating}⭐"