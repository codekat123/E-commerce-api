from .models import Referral,Coupon
from rest_framework.response import Response
from rest_framework import status
from django.urls import reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.exceptions import ValidationError
from product.permissions import IsMerchant
from product.models import Product
from .serializers import CouponSerializer
from rest_framework.generics import (
    CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
)
from django.utils import timezone


class CouponCreateAPIView(CreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsMerchant]

    def perform_create(self, serializer):
        slug = self.kwargs['slug']
        merchant = self.request.user.merchant_profile

        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise ValidationError("This product does not exist.")

        if product.merchant != merchant:
            raise ValidationError("This product does not belong to you.")

        serializer.save(product=product, merchant=merchant)



class CouponListAPIView(ListAPIView):
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsMerchant]

    def get_queryset(self):
        merchant = self.request.user.merchant_profile
        return Coupon.objects.filter(merchant=merchant)


class CouponDetailAPIView(RetrieveAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    lookup_field = 'code'
    permission_classes = [IsAuthenticated]



class CouponUpdateAPIView(UpdateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    lookup_field = 'code'
    permission_classes = [IsAuthenticated, IsMerchant]

    def perform_update(self, serializer):
        coupon = self.get_object()
        merchant = self.request.user.merchant_profile
        if coupon.merchant != merchant:
            raise ValidationError("You cannot update a coupon that isn’t yours.")
        serializer.save()



class CouponDeleteAPIView(DestroyAPIView):
    queryset = Coupon.objects.all()
    lookup_field = 'code'
    permission_classes = [IsAuthenticated, IsMerchant]

    def perform_destroy(self, instance):
        merchant = self.request.user.merchant_profile
        if instance.merchant != merchant:
            raise ValidationError("You cannot delete a coupon that isn’t yours.")
        instance.delete()



class ApplyCouponAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_slug = request.data.get('product_slug')
        coupon_code = request.data.get('coupon_code')

        if not product_slug or not coupon_code:
            raise ValidationError("Product slug and coupon code are required.")


        try:
            product = Product.objects.get(slug=product_slug)
        except Product.DoesNotExist:
            raise ValidationError("Product does not exist.")

 
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
        except Coupon.DoesNotExist:
            raise ValidationError("Invalid coupon code.")

 
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            raise ValidationError("This coupon is expired or not yet valid.")


        if coupon.product != product:
            raise ValidationError("This coupon is not valid for this product.")


        discount_percentage = coupon.discount
        discounted_price = product.price - (product.price * discount_percentage / 100)

        return Response({
            "product": product.name,
            "original_price": product.price,
            "discount_percentage": discount_percentage,
            "discounted_price": round(discounted_price, 2),
            "message": "Coupon applied successfully!"
        })
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_referral_link(request):
    user = request.user


    profile = getattr(user, "profile", None)
    if not profile:
        return Response(
            {"detail": "User not found."},
            status=status.HTTP_400_BAD_REQUEST
        )

    referral, _ = Referral.objects.get_or_create(referrer=profile)


    protocol = "https" if request.is_secure() else "http"
    domain = request.get_host()
    signup_path = reverse("account:sign-up")
    referral_link = f"{protocol}://{domain}{signup_path}?ref={referral.referral_code}"

    return Response(
        {"referral_link": referral_link},
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_referral_balance(request):
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return Response({'detail': 'User profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

    referral = Referral.objects.filter(referrer=profile).first()
    if not referral:
        return Response({'balance': 0}, status=status.HTTP_200_OK)

    return Response({'balance': referral.reward_given}, status=status.HTTP_200_OK)