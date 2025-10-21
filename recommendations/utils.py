from django.db.models import Sum, Case, When, IntegerField
from .models import UserAction
import pandas as pd

def get_weighted_interactions():
    weights = Case(
        When(action='view', then=1),
        When(action='add_to_cart', then=3),
        When(action='purchase', then=5),
        default=0,
        output_field=IntegerField(),
    )

    qs = (
        UserAction.objects.values('user_id', 'product_id')
        .annotate(total_weight=Sum(weights))
        .exclude(user_id__isnull=True)
        .exclude(product_id__isnull=True)
    )

    return list(qs)

def build_item_user_matrix():
    interactions = get_weighted_interactions()
    df = pd.DataFrame(interactions)
    if df.empty:
        return pd.DataFrame()

    matrix = df.pivot_table(
        index='product_id',
        columns='user_id',
        values='total_weight',
        fill_value=0
    )
    return matrix
