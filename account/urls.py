from django.urls import path ,include
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'account'


urlpatterns = [
    path('login/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('sign-up/',SignUpAPIView.as_view(),name='sign-up'),
    path('logout/',LogoutView.as_view(),name='logout'),

    path('activation/<uidb64>/<token>/', ActivationView.as_view(), name="verify_email"),
    path('resetpassword/', ResetPasswordView.as_view(), name="password"),
    path('comfirm/resetpassword/<uidb64>/<token>/', ConfirmResetPassword.as_view(), name="resetpassword"),


]
