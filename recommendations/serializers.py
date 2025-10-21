from rest_framework import serializers
from .models import ItemSimilarity


class ItemSimilaritySerailizer(serializers.ModelSerializer):
     class Meta:
          model = ItemSimilarity
          fields = '__all__'