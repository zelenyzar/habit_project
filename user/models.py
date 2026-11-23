from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """Менеджер пользователя с обязательным email."""

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        return super().create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )


class User(AbstractUser):
    email = models.EmailField(unique=True)

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    city = models.CharField("Город", max_length=100, blank=True)
    tg_chat_id = models.CharField(
        "Telegram chat_id",
        max_length=64,
        blank=True,
        default="",
    )

    def __str__(self):
        return f"Profile of {self.user.username}"
