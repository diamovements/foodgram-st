from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from foodgram.models import Recipe


User = get_user_model()


class UserAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user1", email="email1@example.com", password="Pass123!@#", first_name="First", last_name="User"
        )
        self.other_user = User.objects.create_user(
            username="user2", email="email2@example.com", password="Pass456!@#", first_name="Second", last_name="User"
        )

    def test_register_user(self):
        url = reverse("users:users-list")
        data = {
            "username": "user3",
            "email": "user3@example.com",
            "password": "Pass789!@#",
            "first_name": "Third",
            "last_name": "User",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="user3").exists())

    def test_register_user_without_email(self):
        url = reverse("users:users-list")
        data = {
            "username": "no_email",
            "password": "Pass123!@#",
            "first_name": "No",
            "last_name": "Email",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_existing_email(self):
        url = reverse("users:users-list")
        data = {
            "username": "existing_email",
            "email": "email1@example.com",
            "password": "Pass123!@#",
            "first_name": "Existing",
            "last_name": "Email",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_profile(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("users:users-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "user1")

    def test_get_profile_unauthorized(self):
        url = reverse("users:users-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_set_password(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("users:set_password")
        data = {"current_password": "Pass123!@#", "new_password": "Pass456!@#"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Pass456!@#"))

    def test_set_password_wrong_current(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("users:set_password")
        data = {"current_password": "WrongPass123!@#", "new_password": "Pass456!@#"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_to_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("users:users-subscribe", args=[self.other_user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.user.follower.filter(author=self.other_user).exists())

    def test_subscribe_to_self(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("users:users-subscribe", args=[self.user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_subscriptions(self):
        self.client.force_authenticate(user=self.user)
        subscribe_url = reverse("users:users-subscribe", args=[self.other_user.id])
        self.client.post(subscribe_url)
        url = reverse("users:users-subscriptions")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.other_user.id)

    def test_get_subscriptions_with_recipes(self):
        self.client.force_authenticate(user=self.user)
        recipe = Recipe.objects.create(
            author=self.other_user,
            name="Test Recipe",
            text="Test Description",
            cooking_time=30
        )
        subscribe_url = reverse("users:users-subscribe", args=[self.other_user.id])
        self.client.post(subscribe_url)
        url = reverse("users:users-subscriptions")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(len(response.data["results"][0]["recipes"]), 1)
        self.assertEqual(response.data["results"][0]["recipes"][0]["id"], recipe.id)
