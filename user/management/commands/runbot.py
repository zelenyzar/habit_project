import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

API_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


class Command(BaseCommand):
    help = "Запуск Telegram-бота в режиме long polling"

    def handle(self, *args, **options):
        offset = 0
        self.stdout.write(self.style.SUCCESS("Бот запущен, жду сообщений..."))

        while True:
            try:
                response = requests.get(
                    f"{API_URL}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                    timeout=35,
                )
                updates = response.json().get("result", [])
            except requests.RequestException as e:
                self.stderr.write(f"Ошибка сети: {e}")
                continue

            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message")
                if not message or not message.get("text"):
                    continue

                chat_id = message["chat"]["id"]
                text = message["text"].strip()

                if text == "/start":
                    requests.post(
                        f"{API_URL}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": "Привет! Отправьте мне ваш email, "
                            "чтобы я мог привязать напоминания о привычках.",
                        },
                        timeout=10,
                    )
                    continue

                # ищем пользователя по email
                user = User.objects.filter(email=text).first()
                if user is None:
                    requests.post(
                        f"{API_URL}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": "Пользователь с таким email не найден. "
                            "Попробуйте ещё раз.",
                        },
                        timeout=10,
                    )
                    continue

                profile, _ = user.profile if hasattr(user, "profile") else (
                    __import__("user.models", fromlist=["UserProfile"]).UserProfile.objects.get_or_create(user=user)
                )
                profile.tg_chat_id = str(chat_id)
                profile.save()

                requests.post(
                    f"{API_URL}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": f"Готово, {user.username}! Теперь я буду "
                        "присылать вам напоминания о привычках.",
                    },
                    timeout=10,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Привязан chat_id {chat_id} к {user.email}")
                )
