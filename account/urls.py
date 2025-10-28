from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    SignUpAPIView,
    LogoutView,
    VerifyOTPAPIView,
    ResetPasswordView,
    ConfirmResetPassword,
    ResendOTPAPIView,
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

    # Password reset
    path('reset-password/', ResetPasswordView.as_view(), name='request_password_reset'),
    path('reset-password/<uidb64>/<token>/', ConfirmResetPassword.as_view(), name='resetpassword'),
]

