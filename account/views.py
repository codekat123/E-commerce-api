from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import UserRateThrottle
from .serializers import *
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode , urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings


class SignUpAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]
    authentication_classes = []
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save(is_active=False)
        
        if user.roles == "Merchant":
            user.is_active = True
            user.save()
            return user

        protocol = "https" if self.request.is_secure() else "http"
        domain = self.request.get_host()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        activation_link = f"{protocol}://{domain}{reverse('account:verify_email', kwargs={'uidb64': uid, 'token': token})}"
        subject = "Please activate your email"
        message = (
            f"Please click the link below to activate your account:\n\n"
            f"{activation_link}\n\n"
            "If this email wasn’t intended for you, just ignore it."
        )

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            print(f"Failed to send email: {e}")

        return user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
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
        
        if user.is_active:
            return Response(
                {
                    "success": False,
                    "message": "Your account is already activated.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )



        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response(
                {
                    "success": True,
                    "message": "Your account has been activated successfully 🎉",
                    "next_step": "You can now log in and access your dashboard."
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "success": False,
                "message": "Invalid or expired activation link.",
                "next_step": "Try signing up again."
            },
            status=status.HTTP_400_BAD_REQUEST
        )





class ResetPasswordView(APIView):
    """
    Handles password reset requests.
    Sends an email with a secure token-based link to reset the password.
    """

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success": True, "message": "If this email is registered, a reset link was sent."},
                status=status.HTTP_200_OK
            )

        # Build secure reset link
        protocol = "https" if request.is_secure() else "http"
        domain = request.get_host()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{protocol}://{domain}{reverse('account:resetpassword', kwargs={'uidb64': uid, 'token': token})}"

        subject = "Reset Your Password"
        message = (
            f"Hi {user.first_name or 'there'},\n\n"
            f"You requested to reset your password. Click the link below:\n"
            f"{reset_link}\n\n"
            "If you didn’t make this request, just ignore this email."
        )

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            return Response(
                {"success": False, "message": f"Failed to send email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"success": True, "message": "Password reset link sent successfully."},
            status=status.HTTP_200_OK
        )






class ConfirmResetPassword(APIView):
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


        