from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

MANAGER_EMAIL = "manager@example.com"
MANAGER_PASSWORD = "123qwe!"


class Command(BaseCommand):
    help = "Создание менеджера (is_staff=True) с заданными email и паролем"

    def handle(self, *args, **options):
        email = MANAGER_EMAIL
        password = MANAGER_PASSWORD

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Пользователь с email {email} уже существует")
            )
            return

        User.objects.create_user(
            username=email,
            email=email,
            password=password,
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Менеджер {email} создан"))
