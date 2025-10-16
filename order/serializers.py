from rest_framework import serializers
from .models import Order , OrderStatus , OrderPayment
import re

class OrderSerializer(serializers.ModelSerializer):
     class Meta:
          model = Order
          fields = ['first_name','last_name','city','address','email','created_at','update_at','paid','postal_code']


class OrderStatusSerializer(serializers.ModelSerializer):
     class Meta:
          model = OrderStatus
          fields = '__all__'



class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
          model = OrderPayment
          fields = '__all__'
     
    def validate_phone_number(self, value):
        pattern = r'^\+?\d{9,15}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Enter a valid phone number (9–15 digits).")
        return value

    def validate(self, data):
        business_name = data.get('business_name', '').strip().lower()
        owner_name = data.get('owner_name', '').strip().lower()

        if business_name == owner_name:
            raise serializers.ValidationError("Business name and owner name cannot be the same.")
        return data

    def validate_logo(self, value):
        max_size_mb = 2
        if value and value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError("Logo file size must be under 2MB.")
        return value