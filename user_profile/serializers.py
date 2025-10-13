import re
from rest_framework import serializers
from .models import CustomerProfile, MerchantProfile

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'
        read_only_fields =['user']

    def validate_phone_number(self, value):
        # simple phone number pattern (e.g. +201234567890 or 01234567890)
        pattern = r'^\+?\d{9,15}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError("Enter a valid phone number (9–15 digits).")
        return value

    def validate(self, data):
        first_name = data.get('first_name', '').strip().lower()
        last_name = data.get('last_name', '').strip().lower()

        if first_name == last_name:
            raise serializers.ValidationError("First name and last name cannot be the same.")
        return data

    def validate_profile_picture(self, value):
        max_size_mb = 2  # limit to 2MB
        if value and value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError("Profile picture size must be under 2MB.")
        return value
    
class MerchantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantProfile
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