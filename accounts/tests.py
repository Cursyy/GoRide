from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import CustomUser
from subscriptions.models import  UserSubscription
from stats.models import UserStatistics
from django.contrib.auth.models import Group

CustomUser = get_user_model()

class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        # Використовуємо force_login для гарантії аутентифікації
        self.client.force_login(self.user)

    def test_signup_view_get(self):
        self.client.logout()
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_signup_view_post_success(self):
        self.client.logout()
        response = self.client.post(reverse("accounts:signup"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:email_sent"))
        user = CustomUser.objects.get(username="newuser")
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Confirm Your Email Address", mail.outbox[0].subject)

    def test_signup_view_existing_email(self):
        self.client.logout()
        response = self.client.post(reverse("accounts:signup"), {
            "username": "anotheruser",
            "email": "test@example.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Custom user with this Email already exists")

    def test_confirm_email_success(self):
        self.client.logout()
        inactive_user = CustomUser.objects.create_user(
            username="inactive",
            email="inactive@example.com",
            password="password123",
            is_active=False
        )
        token = urlsafe_base64_encode(force_bytes(inactive_user.pk))
        response = self.client.get(reverse("accounts:confirm_email", args=[token]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("main:home"))
        inactive_user.refresh_from_db()
        self.assertTrue(inactive_user.is_active)
        self.assertTrue(self.client.session.get('_auth_user_id'))
        self.assertTrue(inactive_user.groups.filter(name="Customer").exists())  # Перевірка через groups
        self.assertTrue(UserStatistics.objects.filter(user=inactive_user).exists())

    def test_confirm_email_invalid_token(self):
        self.client.logout()
        response = self.client.get(reverse("accounts:confirm_email", args=["invalidtoken"]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("main:home"))

    def test_email_sent_view(self):
        response = self.client.get(reverse("accounts:email_sent"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/email_sent.html")

    def test_profile_view(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")
        self.assertContains(response, "testuser")
        self.assertEqual(response.context["user"], self.user)

    def test_profile_edit_get(self):
        response = self.client.get(reverse("accounts:profile_edit"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_edit.html")
        self.assertIn("form", response.context)

    def test_profile_edit_post(self):
        response = self.client.post(reverse("accounts:profile_edit"), {
            "username": "updateduser",
            "email": "updated@example.com",
            "phone_num": "123456789"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.phone_num, "123456789")