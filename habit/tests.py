from datetime import time

import requests_mock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from habit.models import Habit
from user.models import User


def make_habit(user, **overrides):
    data = {
        "user": user,
        "place": "Дом",
        "time": time(7, 30),
        "action": "Выпить стакан воды",
        "is_pleasant": True,
        "periodicity": 1,
        "duration_minutes": 1,
        "is_public": False,
    }
    data.update(overrides)
    return Habit.objects.create(**data)


HABIT_PAYLOAD = {
    "place": "Парк",
    "time": "07:00:00",
    "action": "Утренняя пробежка",
    "periodicity": 1,
    "duration_minutes": 2,
}


class HabitAuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )
        self.url = "/api/habits/"

    def test_anonymous_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_habit_belongs_to_current_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, HABIT_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        habit = Habit.objects.get(id=response.data["id"])
        self.assertEqual(habit.user, self.user)


class HabitOwnerPermissionTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )
        self.stranger = User.objects.create_user(
            username="boris", email="boris@example.com", password="Qwerty12345!"
        )
        self.habit = make_habit(self.owner)
        self.detail_url = f"/api/habits/{self.habit.id}/"

    def test_list_shows_only_own_habits(self):
        make_habit(self.stranger)
        self.client.force_authenticate(user=self.owner)
        response = self.client.get("/api/habits/")
        ids = [h["id"] for h in response.data["results"]]
        self.assertIn(self.habit.id, ids)
        self.assertEqual(len(ids), 1)

    def test_stranger_cannot_patch(self):
        self.client.force_authenticate(user=self.stranger)
        response = self.client.patch(self.detail_url, {"place": "Лес"})
        self.assertIn(
            response.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.place, "Дом")

    def test_stranger_cannot_delete(self):
        self.client.force_authenticate(user=self.stranger)
        response = self.client.delete(self.detail_url)
        self.assertIn(
            response.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )
        self.assertTrue(Habit.objects.filter(id=self.habit.id).exists())

    def test_owner_can_edit_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"place": "Лес"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit.refresh_from_db()
        self.assertEqual(self.habit.place, "Лес")

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=self.habit.id).exists())


class PublicHabitsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )
        self.other = User.objects.create_user(
            username="boris", email="boris@example.com", password="Qwerty12345!"
        )
        self.public_habit = make_habit(self.other, is_public=True)
        self.private_habit = make_habit(self.other, is_public=False)
        self.url = "/api/habits/public/"

    def test_public_list_shows_only_public_habits(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        ids = [h["id"] for h in response.data["results"]]
        self.assertIn(self.public_habit.id, ids)
        self.assertNotIn(self.private_habit.id, ids)

    def test_public_list_denies_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_public_endpoint_rejects_delete(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_stranger_cannot_edit_public_habit_via_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f"/api/habits/{self.public_habit.id}/", {"place": "Лес"}
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN),
        )


class HabitValidationTests(APITestCase):
    """Границы валидаторов подгоните под свой код:
    здесь по требованиям — периодичность не больше 7, длительность не больше 2 минут."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )
        self.client.force_authenticate(user=self.user)
        self.url = "/api/habits/"

    def test_periodicity_over_limit_rejected(self):
        response = self.client.post(self.url, {**HABIT_PAYLOAD, "periodicity": 8})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duration_over_limit_rejected(self):
        response = self.client.post(self.url, {**HABIT_PAYLOAD, "duration_minutes": 3})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reward_and_related_habit_mutually_exclusive(self):
        reward_habit = make_habit(self.user, is_public=True)
        response = self.client.post(
            self.url,
            {**HABIT_PAYLOAD, "reward": "Кофе", "related_habit_id": reward_habit.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_related_habit_must_be_pleasant(self):
        unpleasant = make_habit(self.user, is_pleasant=False)
        response = self.client.post(
            self.url, {**HABIT_PAYLOAD, "related_habit_id": unpleasant.id}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HabitPaginationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )
        for i in range(7):
            make_habit(self.user, action=f"Привычка {i}", time=time(7, i))
        self.client.force_authenticate(user=self.user)
        self.url = "/api/habits/"

    def test_page_size_default_is_five(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])

    def test_page_size_param_cannot_exceed_max(self):
        response = self.client.get(self.url, {"page_size": 100})
        self.assertLessEqual(len(response.data["results"]), 50)


class TelegramReminderTaskTests(APITestCase):
    def test_reminder_sent_to_linked_user(self):
        from habit.tasks import send_habit_reminder
        from user.models import UserProfile

        user = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.tg_chat_id = "12345"
        profile.save()
        habit = make_habit(user)

        with requests_mock.Mocker() as m:
            m.post(requests_mock.ANY, json={"ok": True})
            send_habit_reminder(habit.id)
            self.assertEqual(m.call_count, 1)
            self.assertIn("12345", m.last_request.text)
