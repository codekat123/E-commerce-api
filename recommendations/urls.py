from django.urls import path
from .views import *
# from .views import RecommendationView, FeedbackView

urlpatterns = [
     path("", UserRecommendationsView.as_view(), name="user-recommendations"),
     path("similar-products/<slug:slug>/",SimilarProduct.as_view(),name='similar-products'),
     path("recent-viewed-products/",RecentViewedProducts.as_view(),name='recent-products'),
     
]


