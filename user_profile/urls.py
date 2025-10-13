from django.urls import path
from .views import (
    CustomerProfileRetrieveAPIView,
    CustomerProfileUpdateAPIView,
    MerchantProfileRetrieveAPIView,
    MerchantProfileUpdateAPIView
)

app_name = 'user_profile'

urlpatterns = [
    # ----- Customer Endpoints -----
    path('customer/', CustomerProfileRetrieveAPIView.as_view(), name='customer-profile-detail'),
    path('customer/update/', CustomerProfileUpdateAPIView.as_view(), name='customer-profile-update'),

    # ----- Merchant Endpoints -----
    path('merchant/', MerchantProfileRetrieveAPIView.as_view(), name='merchant-profile-detail'),
    path('merchant/update/', MerchantProfileUpdateAPIView.as_view(), name='merchant-profile-update'),
]
