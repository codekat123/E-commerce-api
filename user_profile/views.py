from django.shortcuts import render
from rest_framework.generics import UpdateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from .models import CustomerProfile, MerchantProfile
from .serializers import CustomerProfileSerializer, MerchantProfileSerializer


class CustomerProfileUpdateAPIView(UpdateAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = CustomerProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "profile", None)
        if not profile:
            raise NotFound("This user does not have a profile yet.")
        return profile


class CustomerProfileRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "profile", None)
        if not profile:
            raise NotFound("This user does not have a profile yet.")
        return profile


# ------------------- MERCHANT PROFILE VIEWS -------------------

class MerchantProfileUpdateAPIView(UpdateAPIView):
    """
    Allows an authenticated merchant to update their profile.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MerchantProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "merchant_profile", None)
        if not profile:
            raise NotFound("This merchant does not have a profile yet.")
        return profile


class MerchantProfileRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MerchantProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "merchant_profile", None)
        if not profile:
            raise NotFound("This merchant does not have a profile yet.")
        return profile
