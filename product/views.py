from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .permissions import IsAdminOrReadOnly, IsMerchantOrReadOnly


# ---------- Category Views ----------
class CategoryListCreateAPIView(ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoryRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]


# ---------- Product Views ----------
class ProductListCreateAPIView(ListCreateAPIView):
    queryset = Product.objects.select_related('category', 'merchant').all()
    serializer_class = ProductSerializer
    permission_classes = [IsMerchantOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(merchant=self.request.user.merchant_profile)


class ProductRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category', 'merchant').all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    permission_classes = [IsMerchantOrReadOnly]

    def perform_update(self, serializer):
        serializer.save(merchant=self.request.user.merchant_profile)
