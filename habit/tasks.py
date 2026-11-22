import requests

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import Habit

API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


@shared_task
def send_habit_reminder(habit_id):
    """Отправка напоминания о конкретной привычке."""
    habit = Habit.objects.select_related("user__profile").filter(pk=habit_id).first()
    if habit is None:
        return

    chat_id = getattr(habit.user.profile, "tg_chat_id", "")
    if not chat_id:
        return  # пользователь не привязал Telegram

    message = (
        f"⏰ Пора выполнить привычку!\n"
        f"Я буду {habit.action} в {habit.time.strftime('%H:%M')} "
        f"({habit.place})."
    )

    try:
        response = requests.post(
            f"{API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        # не даём падать воркеру из-за сети — логируем
        print(f"Ошибка отправки в Telegram (habit {habit_id}): {e}")


@shared_task
def check_habits():
    """Проверка: какие привычки пора выполнять прямо сейчас.

    Запускается Celery Beat каждые 5 минут.
    """
    now = timezone.localtime()
    current_time = now.time().replace(second=0, microsecond=0)

    for habit in Habit.objects.select_related("user__profile"):
        if habit.time.replace(second=0, microsecond=0) != current_time:
            continue
        # периодичность: считаем, сколько дней прошло с создания привычки
        days_since = (now.date() - habit.created_at.date()).days
        if days_since % habit.periodicity == 0:
            send_habit_reminder.delay(habit.id)
