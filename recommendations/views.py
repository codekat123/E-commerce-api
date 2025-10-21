from rest_framework.generics import ListAPIView
from .models import *
from django.db.models import Q
from .serializers import ItemSimilaritySerailizer
from product.models import Product
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from .models import ItemSimilarity, Product
from product.serializers import ProductSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache


class SimilarProduct(ListAPIView):
    serializer_class = ItemSimilaritySerailizer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        user = self.request.user
        
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return ItemSimilarity.objects.none()  
        

        return ItemSimilarity.objects.filter(product_slug=product.slug)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({'message': 'No similar products found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)






class UserRecommendationsView(ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

       
        interacted = (
            UserAction.objects.filter(user=user, product__isnull=False)
            .values_list("product_id", flat=True)
            .distinct()
        )

        if not interacted:
            return Product.objects.none()

        
        similar_ids = (
            ItemSimilarity.objects
            .filter(product_id__in=interacted)
            .order_by("-score")
            .values_list("similar_product_id", flat=True)[:50]
        )

        
        return Product.objects.filter(id__in=similar_ids).exclude(id__in=interacted)


