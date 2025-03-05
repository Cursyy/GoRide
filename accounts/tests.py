from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

class AccountsTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="testuser", email="test@example.com", password="password123")
        self.client.login(username="testuser", password="password123")

    def test_signup(self):
        response = self.client.post(reverse("accounts:signup"), {
            "username": "testuser2",
            "email": "test2@example.com",
            "password1": "strongpassword123",
            "password2": "strongpassword123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("main:home"))

    def test_login(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 302) 

    def test_logout(self):
        self.client.login(username="testuser", password="strongpassword123")
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)

    def test_password_change(self):
        response = self.client.post(reverse("password_change"), {
            "old_password": "password123",
            "new_password1": "newpassword456",
            "new_password2": "newpassword456"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.login(username="testuser", password="newpassword456"))

    def test_profile_view(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testuser")

    def test_profile_edit(self):
        response = self.client.post(reverse("accounts:profile_edit"), {
            "username": "updateduser",
            "email": "updated@example.com",
            "phone_num": "123456789"
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")
        self.assertEqual(self.user.email, "updated@example.com")
    
    def test_password_reset_email_sent(self):
        response = self.client.post(reverse("password_reset"), {"email": self.user.email})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("password_reset_done"))

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Password reset on", mail.outbox[0].subject)
        self.assertIn(self.user.email, mail.outbox[0].to)