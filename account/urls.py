from django.urls import path
from .views import SignUpAPIView , LogoutView
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
]
