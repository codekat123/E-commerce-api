from rest_framework import serializers
from .models import Coupon
from product.models import Product

class CouponSerializer(serializers.ModelSerializer):
     class Meta:
          model = Coupon
          fields = '__all__'
          read_only_fields = ['id', 'created_at','merchant']
