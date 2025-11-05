from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    SignUpAPIView,
    LogoutView,
    VerifyOTPAPIView,
    SendPasswordResetOTP,
    ResendOTPAPIView,
    VerifyOTPAndReset,
    ResetPassword
)

app_name = 'account'

urlpatterns = [
    # Auth tokens
    path('login/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Registration and logout
    path('sign-up/', SignUpAPIView.as_view(), name='sign-up'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Email verification
    path('activate/', VerifyOTPAPIView.as_view(), name='verify_email'),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),

    path('send/password/reset/', SendPasswordResetOTP.as_view(), name='request-reset'),
    path('password/reset/verify/', VerifyOTPAndReset.as_view(), name='verify-otp'),
    path('password/reset/', ResetPassword.as_view(), name='reset-password'),
]

