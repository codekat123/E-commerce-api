from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer
from .tasks import send_email_task
from .utils import verify_otp, generate_otp, store_otp
from coupon.models import Referral


# ---------------- SIGNUP ---------------- #

class SignUpAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]
    authentication_classes = []
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        """Handle user creation and referral logic."""
        user = serializer.save(is_active=False)
        ref_code = self.request.GET.get('ref')

        if ref_code:
            try:
                referral = Referral.objects.get(referral_code=ref_code)
                Referral.objects.get_or_create(
                    referrer=referral.referrer,
                    referred=user.profile
                )
            except Referral.DoesNotExist:
                pass
        return user

    def create(self, request, *args, **kwargs):
        """Customize response message after registration."""
        response = super().create(request, *args, **kwargs)
        return Response(
            {
                "message": "User created successfully. Please check your email for the OTP.",
                "email": response.data.get("email"),
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------- LOGOUT ---------------- #

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


# ---------------- OTP VERIFICATION ---------------- #

class VerifyOTPAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not all([email, otp]):
            return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        if verify_otp(email, otp):
            user = User.objects.filter(email=email).first()
            if user:
                user.is_active = True
                user.save()
            return Response({"message": "Account verified successfully."}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)


# ---------------- RESEND OTP ---------------- #

class ResendOTPAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Account does not exist."}, status=status.HTTP_404_NOT_FOUND)

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
        return Response({"message": "OTP resent successfully."}, status=status.HTTP_200_OK)


# ---------------- PASSWORD RESET FLOW ---------------- #

class SendPasswordResetOTP(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        otp = generate_otp()
        store_otp(email, otp)

        subject = "Password Reset OTP"
        html_content = f"<h3>Your OTP is: {otp}</h3><p>It expires in 5 minutes.</p>"
        send_email_task(subject=subject, html_content=html_content, recipient_list=[email])

        return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)


class VerifyOTPAndReset(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not all([email, otp]):
            return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        if verify_otp(email, otp):
            cache.set(f'allow_change_{email}', True, timeout=1200)  # 20 minutes
            return Response({"verified": True, "email": email}, status=status.HTTP_200_OK)

        return Response({"verified": False, "error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)


class ResetPassword(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        new_password = request.data.get("new_password")

        if not all([email, new_password]):
            return Response({"error": "Email and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not cache.get(f'allow_change_{email}'):
            return Response({"error": "OTP verification required before changing password."}, status=status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(User, email=email)
        user.set_password(new_password)
        user.save()
        cache.delete(f'allow_change_{email}')

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
