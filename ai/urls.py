from django.urls import path
from .views import AIChatAPIView

urlpatterns = [
    path("", AIChatAPIView.as_view(), name="ai-chat"),
]
