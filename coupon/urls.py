from django.urls import path
from .views import *

app_name = 'coupon'

urlpatterns = [
     path('products/<slug:slug>/coupons/', CouponCreateAPIView.as_view(), name='coupon-create'),
     path('coupons/', CouponListAPIView.as_view(), name='coupon-list'),
     path('coupons/<str:code>/', CouponDetailAPIView.as_view(), name='coupon-detail'),
     path('coupons/<str:code>/update/', CouponUpdateAPIView.as_view(), name='coupon-update'),
     path('coupons/<str:code>/delete/', CouponDeleteAPIView.as_view(), name='coupon-delete'),
     path('apply-coupon/', ApplyCouponAPIView.as_view(), name='apply-coupon'),
     path('get-referral-link/',generate_referral_link,name='get-referral-link'),
     path('get-referral-balance/',get_referral_balance,name='get-referral-balance'),
]