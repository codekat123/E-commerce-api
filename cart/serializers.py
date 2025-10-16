from rest_framework import serializers

class CartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, default=1)

class PaidOrderSerializer(serializers.Serializer):
    is_paid = serializers.BooleanField(required=True)