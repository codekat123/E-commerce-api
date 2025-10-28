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

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .utils import generate_otp, store_otp
from .tasks import send_email_task

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



class ResetPasswordView(APIView):
    """
    Handles password reset requests asynchronously via Celery.
    """
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Respond the same to prevent info leaks
            return Response(
                {"success": True, "message": "If this email is registered, a reset link was sent."},
                status=status.HTTP_200_OK
            )

        protocol = "https" if request.is_secure() else "http"
        domain = request.get_host()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{protocol}://{domain}{reverse('account:resetpassword', kwargs={'uidb64': uid, 'token': token})}"

        subject = "Reset Your Password"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Password Reset Request 🔒</h2>
                <p>Hi {user.first_name or 'there'},</p>
                <p>We received a request to reset your password. Click below to continue:</p>
                <a href="{reset_link}" 
                   style="display:inline-block; padding:10px 20px; background:#28a745; color:white; border-radius:6px; text-decoration:none;">
                   Reset Password
                </a>
                <p style="margin-top:20px;">If you didn’t request this, you can safely ignore it.</p>
            </body>
        </html>
        """

        send_email_task.delay(subject, html_content, [user.email])

        return Response(
            {"success": True, "message": "Password reset link sent successfully."},
            status=status.HTTP_200_OK
        )


class ConfirmResetPassword(APIView):
    
    def get(self, request, uidb64, token):
        return Response({"message": "Send a POST request with the new password."})

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"success": False, "message": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"success": False, "message": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(
                {"success": True, "message": "Password reset successfully."},
                status=status.HTTP_200_OK
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
