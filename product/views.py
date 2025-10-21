from django.core.cache import cache
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView , ListAPIView,RetrieveAPIView,CreateAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Product , ProductRating
from .serializers import CategorySerializer, ProductSerializer,ProductRatingSerializer
from .permissions import IsAdminOrReadOnly, IsMerchant
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from recommendations.task import log_user_action



# ---------- Category Views ----------
class CategoryListCreateAPIView(ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [UserRateThrottle]


    def get_queryset(self):
        cache_key = 'categories_list'
        categories = cache.get(cache_key)
        if not categories:
            categories = list(Category.objects.all())
            cache.set(cache_key, categories, timeout=60 * 30)  
        return categories


class CategoryRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [UserRateThrottle]


    def perform_update(self, serializer):
        response = super().perform_update(serializer)
        cache.delete('categories_list')  # invalidate cache
        return response

    def perform_destroy(self, instance):
        response = super().perform_destroy(instance)
        cache.delete('categories_list')
        return response


# ---------- Product Views ----------
class ProductListAPIView(ListAPIView):
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        category_slug = self.request.query_params.get('category')
        cache_key = f'products_{category_slug or "all"}'
        products = cache.get(cache_key)

        if not products:
            queryset = Product.objects.select_related('category', 'merchant').all()
            if category_slug:
                queryset = queryset.filter(category__slug=category_slug)
            products = list(queryset)
            cache.set(cache_key, products, timeout=60 * 5)
        return products



class ProductRetrieveAPIView(RetrieveAPIView):
    queryset = Product.objects.select_related('category', 'merchant').all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    throttle_classes = [UserRateThrottle]
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().retrieve(request, *args, **kwargs)

        try:
            session_id = getattr(request.session, 'session_key', None)
            user_id = request.user.id if request.user and request.user.is_authenticated else None
            log_user_action.delay(
                user_id=user_id,
                product_id=instance.id,
                action='view',
                session_id=session_id,
                metadata={'source': 'product_detail', 'slug': instance.slug}
            )
        except Exception:
            pass

        return response



class ProductRatingListCreateAPIView(ListCreateAPIView):
    serializer_class = ProductRatingSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        slug = self.kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        return ProductRating.objects.filter(product=product)

    def perform_create(self, serializer):
        slug = self.kwargs['slug']
        product = get_object_or_404(Product, slug=slug)
        user = self.request.user

        if hasattr(user, 'profile'):
            serializer.save(user=user.profile, product=product)
        else:
            raise ValidationError({"detail": "User profile not found."})

        


