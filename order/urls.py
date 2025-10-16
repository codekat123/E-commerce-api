from django.urls import path
from .views import *

app_name = 'order'

urlpatterns = [
     path('create/',ConfirmOrder.as_view(),name='confirm'),
     path('track-order/<order_id>/',TrackOrder.as_view(),name='status'),
     path('order-payment/<order_id>/',OrderPaymentView.as_view(),name='status'),
]