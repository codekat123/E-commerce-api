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


class SignUpAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]
    authentication_classes = []
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)

        if user.roles == "merchant":
            user.is_active = True
            user.save()
            return user

        protocol = "https" if self.request.is_secure() else "http"
        domain = self.request.get_host()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_link = f"{protocol}://{domain}{reverse('account:verify_email', kwargs={'uidb64': uid, 'token': token})}"

        subject = "Activate Your ShopAI Account"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Welcome to <strong>ShopAI</strong> 👋</h2>
                <p>Click the button below to verify your email and activate your account:</p>
                <a href="{activation_link}" 
                   style="display:inline-block; padding:10px 20px; background:#007BFF; color:white; border-radius:6px; text-decoration:none;">
                   Activate Account
                </a>
                <p style="margin-top:20px;">If this wasn’t you, please ignore this email.</p>
            </body>
        </html>
        """

        send_email_task.delay(subject, html_content, [user.email])
        return user

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


class ActivationView(APIView):
    def get(self, request, uidb64, token):
        try:
            user_id = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(id=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and user.is_active:
            return Response(
                {"success": False, "message": "Your account is already activated."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response(
                {"success": True, "message": "Your account has been activated successfully 🎉"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"success": False, "message": "Invalid or expired activation link."},
            status=status.HTTP_400_BAD_REQUEST
        )


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
