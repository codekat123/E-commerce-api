from celery import shared_task
from django.contrib.auth import get_user_model
from product.models import Product
from order.models import OrderItem
from .models import *
from django.db import transaction
from django.db.models import Count
from collections import defaultdict
from math import sqrt

User = get_user_model()

@shared_task(bind=True, max_retries=3)
def log_user_action(self, user_id=None, product_id=None, order_item_id=None, action='view', session_id=None, metadata=None, timestamp=None):
    """
    Asynchronously create a UserAction record.
    Pass ids (not model instances) to avoid serialization issues.
    """
    user = None
    product = None
    order_item = None

    try:
        if user_id:
            user = User.objects.filter(pk=user_id).first()
        if product_id:
            product = Product.objects.filter(pk=product_id).first()
        if order_item_id:
            order_item = OrderItem.objects.filter(pk=order_item_id).first()

        ua = UserAction.objects.create(
            user=user,
            product=product,
            order_item=order_item,
            action=action,
            session_id=session_id,
            metadata=metadata or {}
        )
        return ua.pk
    except Exception as e:
        self.retry(exc=e, countdown=10)
        return f"Email sending failed: {e}"

@shared_task
def compute_item_similarity(model_version="v1"):
    """
    Build a simple item-based collaborative-filtering matrix from UserAction.
    """

    print("[Task] Building item similarity matrix...")


    actions = (
        UserAction.objects
        .filter(action__in=["view", "purchase","add_to_cart"])
        .values("user_id", "product_id")
        .distinct()
    )


    user_products = defaultdict(set)
    for row in actions:
        if row["user_id"] and row["product_id"]:
            user_products[row["user_id"]].add(row["product_id"])


    co_counts = defaultdict(lambda: defaultdict(int))
    product_counts = defaultdict(int)

    for products in user_products.values():
        for p in products:
            product_counts[p] += 1
            for q in products:
                if p != q:
                    co_counts[p][q] += 1

    similarities = []
    for p, related in co_counts.items():
        for q, count in related.items():
            score = count / sqrt(product_counts[p] * product_counts[q])
            similarities.append((p, q, round(score, 4)))


    with transaction.atomic():
        ItemSimilarity.objects.filter(model_version=model_version).delete()
        bulk = [
            ItemSimilarity(
                product_id=p,
                similar_product_id=q,
                score=score,
                model_version=model_version,
            )
            for (p, q, score) in similarities if score > 0
        ]
        ItemSimilarity.objects.bulk_create(bulk, batch_size=5000)

    print(f"[Task] Stored {len(bulk)} similarity pairs.")
    return len(bulk)