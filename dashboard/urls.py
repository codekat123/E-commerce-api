from django.urls import path
from .views import (
    MerchantOrderedProductsView,
    MerchantPaidProductsView,
    MerchantCreateProductsView,
    MerchantUpdateProductsView,
    MerchantChartDataView,
    GenerateReport,
)

app_name = 'dashboard'

urlpatterns = [
    # List all products that were ordered (at least once)
    path('products/ordered/', MerchantOrderedProductsView.as_view(), name='ordered-products'),

    # List all products that have been paid for
    path('products/paid/', MerchantPaidProductsView.as_view(), name='paid-products'),

    # Create a new product (for merchants)
    path('products/create/', MerchantCreateProductsView.as_view(), name='create-product'),

    # Update an existing product by its slug
    path('products/<slug:slug>/update/', MerchantUpdateProductsView.as_view(), name='update-product'),

    # Get chart
    path('chart/',MerchantChartDataView.as_view(),name='chart'),

    path("report/<str:report_type>/", GenerateReport.as_view(), name="generate-report"),
]
