from django.urls import path
from .views import *


app_name = 'product'

urlpatterns = [
    # ---- Category endpoints ----
    path('categories/', CategoryListCreateAPIView.as_view(), name='category-list-create'),
    path('categories/<slug:slug>/', CategoryRetrieveUpdateDestroyAPIView.as_view(), name='category-detail'),

    # ---- Product endpoints ----
    path('products/', ProductListAPIView.as_view(), name='product-list-create'),
    path('products/<slug:slug>/', ProductRetrieveAPIView.as_view(), name='product-detail'),

]
