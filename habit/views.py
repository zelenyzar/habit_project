from rest_framework import viewsets, permissions
from rest_framework.decorators import action

from .models import Habit
from .permissions import IsOwner
from .serializers import HabitSerializer
from .pagination import HabitListPagination


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    pagination_class = HabitListPagination
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    # --- Личные привычки (CRUD) ---
    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # --- Публичные привычки (только чтение) ---
    @action(detail=False, methods=['get'])
    def public(self, request):
        queryset = Habit.objects.filter(is_public=True).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            page if page is not None else queryset, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
