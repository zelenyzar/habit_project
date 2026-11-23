from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from habit.models import Habit

User = get_user_model()


class Command(BaseCommand):
    help = "Наполнение базы тестовыми данными (идемпотентно)"

    def handle(self, *args, **options):
        if User.objects.filter(username="anna").exists():
            self.stdout.write(
                self.style.WARNING("Тестовые данные уже есть в базе — ничего не создаю")
            )
            return

        anna = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )
        boris = User.objects.create_user(
            username="boris", email="boris@example.com", password="Qwerty12345!"
        )

        pleasant_water = Habit.objects.create(
            user=anna,
            place="Дом",
            time=time(7, 30),
            action="Выпить стакан воды",
            is_pleasant=True,
            periodicity=1,
            duration_minutes=1,
            is_public=True,
        )
        Habit.objects.create(
            user=anna,
            place="Парк",
            time=time(7, 0),
            action="Утренняя пробежка 30 минут",
            periodicity=1,
            duration_minutes=2,
            related_habit=pleasant_water,
        )
        Habit.objects.create(
            user=boris,
            place="Спортзал",
            time=time(19, 0),
            action="Силовая тренировка",
            periodicity=2,
            reward="Молочный коктейль",
            duration_minutes=2,
        )

        self.stdout.write(self.style.SUCCESS(f"Создано пользователей: 2, привычек: 3"))
