from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import CustomUser
from stats.models import UserStatistics
from subscriptions.models import UserSubscription
from booking.models import Booking
from avatar.models import UserAvatar, AvatarItem

User = get_user_model()

class AccountsViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            is_active=True
        )
        self.group = Group.objects.create(name="Customer")
        self.user.groups.add(self.group)

    def test_signup_view(self):
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_confirm_email_valid_token(self):
        self.user.is_active = False
        self.user.save()
        token = self.user.pk  # Simulate a valid token
        response = self.client.get(reverse("accounts:confirm_email", args=[token]))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertRedirects(response, reverse("main:home"))

    def test_confirm_email_invalid_token(self):
        response = self.client.get(reverse("accounts:confirm_email", args=["invalid-token"]))
        self.assertRedirects(response, reverse("main:home"))

    def test_email_sent_view(self):
        response = self.client.get(reverse("accounts:email_sent"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/email_sent.html")

    def test_profile_view_authenticated(self):
        self.client.login(email="testuser@example.com", password="password123")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")

    def test_profile_view_unauthenticated(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:profile')}")

    def test_profile_edit_view_get(self):
        self.client.login(email="testuser@example.com", password="password123")
        response = self.client.get(reverse("accounts:profile_edit"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile_edit.html")

    def test_profile_edit_view_post(self):
        self.client.login(email="testuser@example.com", password="password123")
        response = self.client.post(reverse("accounts:profile_edit"), {
            "email": "updateduser@example.com",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updateduser@example.com")
        self.assertRedirects(response, reverse("accounts:profile"))