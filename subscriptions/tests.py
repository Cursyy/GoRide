from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, UserSubscription

CustomUser = get_user_model()

class SubscriptionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.plan = SubscriptionPlan.objects.create(
            type="Monthly",
            price=50.00,
            duration_days=30,
            max_ride_hours=20
        )

    def test_subscription_plans_view(self):
        self.client.force_login(self.user) 
        response = self.client.get(reverse("subscriptions:subscription_plans"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plans.html")
        self.assertIn(self.plan, response.context["plans"])

    def test_subscribe_user_new_subscription(self):
        self.client.force_login(self.user) 
        response = self.client.get(reverse("subscriptions:subscribe_user", args=[self.plan.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("subscriptions:subscription_success"))
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertTrue(subscription.is_active())

    def test_subscribe_user_active_subscription(self):
        self.client.force_login(self.user) 
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        response = self.client.get(reverse("subscriptions:subscribe_user", args=[self.plan.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("subscriptions:subscription_plans"))

    def test_subscription_success_view(self):
        self.client.force_login(self.user) 
        response = self.client.get(reverse("subscriptions:subscription_success"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "success.html")