from rest_framework.generics import CreateAPIView , DestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import UserRateThrottle
from .serializers import *
from .models import User


class SignUpAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    throttle_classes = [UserRateThrottle]
    authentication_classes = []
    permission_classes = [AllowAny]

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
    
class DeleteUserView(DestroyAPIView):
    """
    Allows an authenticated user to delete their own account.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ensures only the logged-in user's account is deleted
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(
            {"message": "Your account has been deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )