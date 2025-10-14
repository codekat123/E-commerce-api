from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import Serializer, IntegerField
from product.models import Product
from rest_framework.throttling import UserRateThrottle
from .serializers import CartItemSerializer 


CACHE_TIMEOUT = 60 * 60 * 24 * 2  # 2 days




class CartService:
    """Handles cache operations for user carts."""

    @staticmethod
    def get_key(user):
        return f"cart_{user.id}"

    @staticmethod
    def get_cart(user):
        return cache.get(CartService.get_key(user), {})

    @staticmethod
    def save_cart(user, cart):
        cache.set(CartService.get_key(user), cart, timeout=CACHE_TIMEOUT)
        return cart


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def list(self, request):
        """Retrieve the current cart."""
        cart = CartService.get_cart(request.user)
        if not cart:
            return Response({'error': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        total_price = sum(item['total_price'] for item in cart.values())
        cart['total_cart_price'] = total_price
        CartService.save_cart(request.user, cart)
        return Response({'cart': cart}, status=status.HTTP_200_OK)

    def create(self, request, slug=None):
        """Add a product to the cart."""
        product = get_object_or_404(Product, slug=slug)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data['quantity']

        cart = CartService.get_cart(request.user)
        if product.id in cart:
            cart[product.id]['quantity'] += quantity
        else:
            cart[product.id] = {
                'name': product.name,
                'quantity': quantity,
                'total_price': product.price * quantity,
            }

        cart[product.id]['total_price'] = product.price * cart[product.id]['quantity']
        CartService.save_cart(request.user, cart)
        return Response({'message': 'Product added.', 'cart': cart}, status=status.HTTP_200_OK)

    def update(self, request, slug=None):
        """Update product quantity."""
        product = get_object_or_404(Product, slug=slug)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data['quantity']

        cart = CartService.get_cart(request.user)
        if product.id not in cart:
            return Response({'error': 'Product not found in cart.'}, status=status.HTTP_404_NOT_FOUND)

        cart[product.id]['quantity'] = quantity
        cart[product.id]['total_price'] = product.price * quantity
        CartService.save_cart(request.user, cart)
        return Response({'message': 'Quantity updated.', 'cart': cart}, status=status.HTTP_200_OK)

    def destroy(self, request, slug=None):
        """Remove a product from the cart."""
        product = get_object_or_404(Product, slug=slug)
        cart = CartService.get_cart(request.user)
        if product.id not in cart:
            return Response({'error': 'Product not in cart.'}, status=status.HTTP_404_NOT_FOUND)

        del cart[product.id]
        CartService.save_cart(request.user, cart)
        return Response({'message': 'Product removed.', 'cart': cart}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['delete'])
    def clear(self,request):
        key = CartService.get_key(request.user)
        cache.delete(key)
        return Response({'message':'cart cleared successfully'})
