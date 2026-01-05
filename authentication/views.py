from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.utils import timezone
from django.db import transaction

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token, created = Token.objects.get_or_create(user=user)
        user_serializer = UserSerializer(user)
        return Response(
            {
                "user": user_serializer.data,
                "token": token.key,
                "message": "User registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        user.last_login = timezone.now()

        ip_address = self.get_client_ip(request)
        if ip_address:
            user.last_login_ip = ip_address

        user.save(update_fields=["last_login", "last_login_ip"])

        token, created = Token.objects.get_or_create(user=user)

        user_serializer = UserSerializer(user)

        return Response(
            {
                "user": user_serializer.data,
                "token": token.key,
                "message": "Login successful",
            },
            status=status.HTTP_200_OK,
        )

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Delete the user's token
            request.user.auth_token.delete()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"message": "Server Error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_serializer = UserSerializer(request.user)
        return Response(
            {"valid": True, "user": user_serializer.data}, status=status.HTTP_200_OK
        )


class RefreshTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            # Create new token
            token = Token.objects.create(user=request.user)
            return Response(
                {"token": token.key, "message": "Token refreshed successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception:
            return Response(
                {"message": "Server Error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
