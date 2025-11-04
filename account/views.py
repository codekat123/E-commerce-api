from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from .serializers import *
from .models import User
from .tasks import send_email_task   
from coupon.models import Referral
from .utils import verify_otp,generate_otp,store_otp




class SignUpAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]
    authentication_classes = []
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        user.is_active = False
        user.save()
        ref_code = self.request.GET.get('ref')
        if ref_code:
            try:
                referral = Referral.objects.get(referral_code=ref_code)
                if not Referral.objects.filter(referrer=referral.referrer, referred=user.profile).exists():
                    Referral.objects.create(
                        referrer=referral.referrer,
                        referred=user.profile
                    )
            except Referral.DoesNotExist:
                pass
        return user

    def create(self, request, *args, **kwargs):
        """
        Overriding create() to customize the response message
        after user registration and OTP sending.
        """
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "message": "User created successfully. Please check your email for the OTP.",
                "email": response.data.get("email"),
            },
            status=status.HTTP_201_CREATED,
        )
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class VerifyOTPAPIView(APIView):
    authentication_classes = [] 
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if verify_otp(email, otp):
            user = User.objects.filter(email=email).first()
            user.is_active = True
            user.save()
            return Response({"message": "Account verified successfully."}, status=200)
        return Response({"message": "Invalid or expired OTP."}, status=400)



class ResendOTPAPIView(APIView):
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"message": "Email is required"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Account does not exist"}, status=400)

        otp = generate_otp()
        store_otp(email, otp)

        subject = "Resend OTP - ShopAI"
        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background: #f9f9f9; padding: 20px;">
            <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 20px;">
              <h2 style="color: #007BFF;">Your new OTP 🔐</h2>
              <p>Here’s your new One-Time Password (OTP) to verify your account:</p>

              <div style="font-size: 24px; font-weight: bold; background: #f0f4ff; color: #007BFF;
                          padding: 10px 0; text-align: center; border-radius: 6px; letter-spacing: 4px;">
                {otp}
              </div>

              <p style="margin-top: 20px;">⚠️ This OTP will expire in <strong>5 minutes</strong>.</p>
              <p>If you didn’t request this, please ignore this email.</p>
            </div>
          </body>
        </html>
        """

        send_email_task(subject=subject, html_content=html_content, recipient_list=[email])

        return Response({"message": "OTP resent successfully"}, status=200)



class SendPasswordResetOTP(APIView):
    authentication_classes = [] 
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        otp = generate_otp()
        store_otp(email,otp)

        subject = "Password Reset OTP"
        html_content = f"<h3>Your OTP is: {otp}</h3><p>It expires in 5 minutes.</p>"
        send_email_task(subject=subject, html_content=html_content, recipient_list=[email])

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTPAndReset(APIView):
    authentication_classes = [] 
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not verify_otp(email, otp):
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)