from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from user.serializers import UserCreateSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class UserListView(generics.ListAPIView):
    """Список пользователей (только для админов)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
