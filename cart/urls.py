from rest_framework.routers import DefaultRouter
from .views import CartViewSet

app_name = 'cart'

router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')

urlpatterns = router.urls
