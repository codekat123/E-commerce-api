from django.urls import path
from .views import (
    CategoryListCreateAPIView,
    CategoryRetrieveUpdateDestroyAPIView,
    ProductListCreateAPIView,
    ProductRetrieveUpdateDestroyAPIView,
    MerchantProductListAPIView,
)

app_name = 'product'

urlpatterns = [
    # ---- Category endpoints ----
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<slug:slug>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),

    # ---- Product endpoints ----
    path('products/', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('products/<slug:slug>/', ProductRetrieveUpdateDestroyAPIView.as_view(), name='product-detail'),
    # ----- merchant products endpoint ----

    path('my-products/',MerchantProductListAPIView.as_view(),name='my-product')
]
