from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

SUPERUSER_EMAIL = "admin@example.com"
SUPERUSER_PASSWORD = "123qwe"


class Command(BaseCommand):
    help = "Создание суперпользователя с заданными email и паролем"

    def handle(self, *args, **options):
        email = SUPERUSER_EMAIL
        password = SUPERUSER_PASSWORD

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"Пользователь с email {email} уже существует")
            )
            return

        User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Суперпользователь {email} создан"))
