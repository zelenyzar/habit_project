from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegisterViewTests(APITestCase):
    def setUp(self):
        self.url = "/api/users/register/"
        self.valid_data = {
            "username": "anna",
            "email": "anna@example.com",
            "password": "Qwerty12345!x",
        }

    def test_register_success(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="anna@example.com").exists())

    def test_register_password_is_hashed(self):
        self.client.post(self.url, self.valid_data)
        user = User.objects.get(email="anna@example.com")
        # сырой пароль не хранится
        self.assertNotEqual(user.password, self.valid_data["password"])
        self.assertTrue(user.check_password(self.valid_data["password"]))

    def test_register_duplicate_email_fails(self):
        self.client.post(self.url, self.valid_data)
        response = self.client.post(
            self.url,
            {
                "username": "boris",
                "email": "anna@example.com",  # уже занят
                "password": "Qwerty12345!x",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_fails(self):
        response = self.client.post(
            self.url,
            {**self.valid_data, "password": "12345678"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_does_not_require_auth(self):
        response = self.client.post(self.url, self.valid_data)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListPermissionTests(APITestCase):
    def setUp(self):
        self.url = "/api/users/"
        self.regular = User.objects.create_user(
            username="anna", email="anna@example.com", password="Qwerty12345!"
        )

    def test_anonymous_denied(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.regular)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TokenObtainTests(APITestCase):
    def setUp(self):
        self.url = "/api/token/obtain/"
        self.credentials = {
            "username": "anna",
            "email": "anna@example.com",
            "password": "Qwerty12345!",
        }
        User.objects.create_user(**self.credentials)

    def test_obtain_token_success(self):
        response = self.client.post(
            self.url,
            {"username": "anna", "password": "Qwerty12345!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_wrong_password(self):
        response = self.client.post(
            self.url,
            {"username": "anna", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
