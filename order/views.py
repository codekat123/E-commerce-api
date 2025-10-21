from django.shortcuts import get_object_or_404
from rest_framework.generics import CreateAPIView
from .models import Order , OrderItem , OrderStatus , OrderPayment
from .serializers import OrderSerializer , OrderStatusSerializer,OrderPaymentSerializer
from cart.views import CartService
from product.models import Product
from rest_framework.generics import CreateAPIView , UpdateAPIView , ListAPIView,RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from product.models import Product
from order.models import Order, OrderItem
from .serializers import OrderSerializer
from cart.views import CartService  
from .tasks import send_mails
from rest_framework.exceptions import NotFound,  ValidationError
from recommendations.task import log_user_action
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class ConfirmOrder(CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        
        order = serializer.save(user=self.request.user)
        cart = CartService.get_cart(self.request.user)
        if not cart:
            raise ValueError("Cart is empty!")
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            item_data = cart.get(product.id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=item_data['total_price'],
            )

        send_mails.delay(order.order_id)
        CartService.clear_cart(self.request.user)

        return order



class OrderUpdateAPIView(UpdateAPIView):
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        order_id = self.kwargs.get('order_id')
        user = self.request.user

        if order_id:
            return get_object_or_404(Order, order_id=order_id, user=user)
        
        order = Order.objects.filter(user=user).order_by('-created_at').first()
        if not order:
            raise NotFound("No orders found for this user.")
        return order








class OrderPaymentView(CreateAPIView):
    queryset = OrderPayment.objects.all()
    serializer_class = OrderPaymentSerializer

    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, order_id=order_id)

        if OrderPayment.objects.filter(order=order).exists():
            raise ValidationError("Order already paid.")

        with transaction.atomic():
            order.paid = True
            order.save()
            order_payment = serializer.save(order=order)

            try:
                session_key = getattr(self.request.session, 'session_key', None)
                log_user_action(
                    user_id=order.user.id,
                    order_item=order.order_item.id,
                    action='purchase',
                    metadata={
                        'source': 'order_payment',
                        'order_payment_id': order_payment.id,
                    },
                )
            except Exception as e:
                logger.warning(f"Log user action failed: {e}")




class OrderDetailAPIView(RetrieveAPIView):
    serializer_class = OrderSerializer
    lookup_field = 'order_id'
    permission_classes = [IsAuthenticated]

    def get_object(self):
        order_id = self.kwargs.get('order_id')
        user = self.request.user

        if order_id:
            return get_object_or_404(Order, order_id=order_id, user=user)
        
        order = Order.objects.filter(user=user).order_by('-created_at').first()
        if not order:
            raise NotFound("No orders found for this user.")
        return order