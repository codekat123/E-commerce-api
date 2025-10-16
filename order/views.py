from django.shortcuts import get_object_or_404
from rest_framework.generics import CreateAPIView
from .models import Order , OrderItem , OrderStatus , OrderPayment
from .serializers import OrderSerializer , OrderStatusSerializer,OrderPaymentSerializer
from cart.views import CartService
from product.models import Product
from rest_framework.generics import CreateAPIView , UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from product.models import Product
from order.models import Order, OrderItem
from .serializers import OrderSerializer
from cart.views import CartService  
from .tasks import send_mails
from rest_framework.exceptions import NotFound,  ValidationError

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



class TrackOrder(UpdateAPIView):
    queryset = OrderStatus.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            return OrderStatus.objects.filter(order__user=self.kwargs['order_id'])
        except Order.DoesNotExist:
            raise NotFound("Order not found.")





class OrderPaymentView(CreateAPIView):
    queryset = OrderPayment.objects.all()
    serializer_class = OrderPaymentSerializer

    def perform_create(self, serializer):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, order_id=order_id)
        order.paid = True
        order.save()
        
        # You could validate that the order isn’t already paid
        if hasattr(order, 'order_payment'):
            raise ValidationError("Order already paid.")

        serializer.save(order=order)

