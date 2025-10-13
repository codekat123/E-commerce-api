from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['slug']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    merchant_name = serializers.ReadOnlyField(source='merchant.user.username')

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price',
            'category', 'category_name', 'merchant', 'merchant_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'merchant', 'created_at', 'updated_at']
