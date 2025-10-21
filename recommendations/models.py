from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from product.models import Product
from order.models import OrderItem

User = get_user_model()

class UserAction(models.Model):
    ACTION_VIEW = 'view'
    ACTION_ADD_TO_CART = 'add_to_cart'
    ACTION_PURCHASE = 'purchase'
    ACTION_SEARCH = 'search'
    ACTION_CLICK = 'click'
    ACTION_DISMISS = 'not_interested'

    ACTION_TYPES = [
        (ACTION_VIEW, 'View'),
        (ACTION_ADD_TO_CART, 'Add to cart'),
        (ACTION_PURCHASE, 'Purchase'),
        (ACTION_SEARCH, 'Search'),
        (ACTION_CLICK, 'Click'),
        (ACTION_DISMISS, 'Not interested'),
    ]

    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommendation_actions'
    )
    product = models.ForeignKey(
        Product, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommendation_actions'
    )
    order_item = models.ForeignKey(
        OrderItem, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommendation_actions'
    )
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True, help_text="Optional additional info (e.g. search query, source)")
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'product']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        user_part = f"user:{self.user_id}" if self.user_id else "anon"
        prod_part = f"product:{self.product_id}" if self.product_id else self.metadata.get('query', '')
        return f"{user_part} {self.action} {prod_part} @ {self.timestamp.isoformat()}"


class ItemSimilarity(models.Model):
    """
    Stores precomputed similarity between two products (e.g. from co-occurrence or embeddings).
    Use this table for fast 'similar items' queries.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similar_to')
    similar_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similar_from')
    score = models.FloatField()
    model_version = models.CharField(max_length=64, default='v1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'similar_product')
        indexes = [
            models.Index(fields=['product', 'score']),
            models.Index(fields=['model_version']),
        ]
        ordering = ['-score']


class UserRecommendations(models.Model):
    """
    Optional: store precomputed top-K recommendations per user for fast serving.
    recommended_product_ids stored as a small array/JSON of product ids in rank order.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recommendations')
    recommended_product_ids = models.JSONField(help_text="Ordered list of recommended product ids", default=list)
    model_version = models.CharField(max_length=64, default='v1')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['model_version']),
        ]
