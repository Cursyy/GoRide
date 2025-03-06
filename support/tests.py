from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Chat, Message

User = get_user_model()


class ChatModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.test", password="testpass"
        )
        self.chat = Chat.objects.create(user=self.user)

    def test_chat_creation(self):
        self.assertEqual(self.chat.user, self.user)
        self.assertTrue(self.chat.is_active)


class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.test", password="testpass"
        )
        self.chat = Chat.objects.create(user=self.user)
        self.message = Message.objects.create(
            chat=self.chat, sender=self.user, content="Test message"
        )

    def test_message_creation(self):
        self.assertEqual(self.message.chat, self.chat)
        self.assertEqual(self.message.sender, self.user)
        self.assertEqual(self.message.content, "Test message")


class UserChatViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.test", password="testpass"
        )
        self.client.login(username="testuser", password="testpass")
        self.chat = Chat.objects.create(user=self.user)

    def test_user_chat_view_get(self):
        response = self.client.get(reverse("support:user_chat"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "support/user_chat.html")
        self.assertContains(response, "Chat with Support")

    def test_user_chat_view_post(self):
        response = self.client.post(
            reverse("support:user_chat"), {"content": "Test message"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Message.objects.filter(content="Test message").exists())
