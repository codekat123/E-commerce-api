from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import Serializer, IntegerField
from product.models import Product
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from .serializers import CartItemSerializer ,PaidOrderSerializer
from recommendations.task import log_user_action
from coupon.models import Coupon
from django.utils import timezone
from rest_framework.exceptions import ValidationError


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
    
    @staticmethod
    def clear_cart(user):
        key = CartService.get_key(user)
        cache.delete(key)


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
        if product.amount < quantity:
            return Response({'error':'the amount you want doesn\'t exist'},status=status.HTTP_404_NOT_FOUND)
        
        product.amount -= quantity
        product.save()

        cart = CartService.get_cart(request.user)
        if product.id in cart:
            cart[product.id]['quantity'] += quantity
            cart[product.id]['total_price'] = product.price * cart[product.id]['quantity']
        else:
            cart[product.id] = {
                'name': product.name,
                'quantity': quantity,
                'total_price': product.price * quantity,
            }
        cart[product.id]['total_price'] = product.price * cart[product.id]['quantity']
        CartService.save_cart(request.user, cart)
        
        
        try:
            session_id = getattr(request.session, 'session_key', None)
            user_id = request.user.id if request.user and request.user.is_authenticated else None
            log_user_action.delay(
                user_id=user_id,
                product_id=product.id,
                action='add_to_cart',
                session_id=session_id,
                metadata={'quantity': quantity, 'source': 'cart_add'}
            )
        except Exception:
            pass


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

      previous_amount = cart[product.id]['quantity']

      if quantity > previous_amount:
          diff = quantity - previous_amount
          if product.amount < diff:
              return Response({'error': 'Not enough stock available.'}, status=status.HTTP_400_BAD_REQUEST)
          product.amount -= diff
      else:
          diff = previous_amount - quantity
          product.amount += diff

      product.save()

      
      cart[product.id]['quantity'] = quantity
      CartService.save_cart(request.user, cart)  

      return Response({'message': 'Cart updated successfully.'})


    
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
    def clear(self, request):
        key = CartService.get_key(request.user)
        cart = CartService.get_cart(request.user)
        
        serializer = PaidOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_paid = serializer.validated_data['is_paid']
    
        if not is_paid and cart:
            product_ids = cart.keys()
            products = Product.objects.filter(id__in=product_ids)
    
            for product in products:
                product.amount += cart[product.id]['quantity']
            Product.objects.bulk_update(products, ['amount'])
        
        cache.delete(key)
        return Response({'message': 'Cart cleared successfully.'})

    @action(detail=False, methods=['post'])
    def apply_coupon(self, request):
        """Apply a coupon to the user's cart."""
        code = request.data.get('coupon_code')
        if not code:
            return Response({'error': 'Coupon code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            coupon = Coupon.objects.get(code=code, active=True)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon code.'}, status=status.HTTP_404_NOT_FOUND)
        
            
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            raise ValidationError("This coupon is expired or not yet valid.")

        cart = CartService.get_cart(request.user)
        if not cart:
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        product_id = coupon.product.id
        if product_id not in cart:
            raise ValidationError("This coupon does not apply to any product in your cart.")

        original_price = cart[product_id]['total_price']
        discount = coupon.discount
        discounted_price = original_price - (original_price * discount / 100)
        difference = original_price - discounted_price

        cart["coupon"] = {
            "code": coupon.code,
            "discount": discount,
            "product": product_id,
            "discounted_price": round(discounted_price, 2),
            "amount_saved": round(difference, 2)
        }

        total_price = sum(item['total_price'] for key, item in cart.items() if isinstance(key, int))
        cart['total_cart_price'] = round(total_price - difference, 2)

        CartService.save_cart(request.user, cart)
        return Response({
            "message": "Coupon applied successfully.",
            "coupon": cart["coupon"],
            "total_cart_price": cart["total_cart_price"]
        }, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'])
    def remove_coupon(self, request):
        """Remove any applied coupon from the cart."""
        cart = CartService.get_cart(request.user)
        if "coupon" not in cart:
            return Response({'error': 'No coupon applied.'}, status=status.HTTP_400_BAD_REQUEST)

        del cart["coupon"]
        total_price = sum(item['total_price'] for key, item in cart.items() if isinstance(key, int))
        cart['total_cart_price'] = total_price
        CartService.save_cart(request.user, cart)
        return Response({
            "message": "Coupon removed.",
            "total_cart_price": total_price
        }, status=status.HTTP_200_OK)
