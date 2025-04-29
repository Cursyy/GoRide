from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, UserSubscription
from django.utils import timezone


class SubscriptionViewsTestCase(TestCase):
    def setUp(self):
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@gmail.com",
            password="testpassword",
            is_active=True,
        )
        self.client.force_login(self.user)

        # Create a subscription plan
        self.plan = SubscriptionPlan.objects.create(
            type="Daily", price=10.0, duration_days=1, max_ride_hours=2
        )

    def test_subscription_plans_view(self):
        # Test the subscription_plans view
        response = self.client.get(reverse("subscriptions:subscription_plans"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "plans.html")
        self.assertIn(self.plan, response.context["plans"])

    def test_subscribe_user_view_new_subscription(self):
        # Test subscribing to a plan when no active subscription exists
        response = self.client.get(
            reverse("subscriptions:subscribe_user", args=[self.plan.id])
        )
        self.assertRedirects(response, reverse("subscriptions:subscription_success"))

        subscription = UserSubscription.objects.get(user=self.user)
        self.assertTrue(subscription.is_active())
        self.assertEqual(subscription.plan, self.plan)

    def test_subscribe_user_view_existing_active_subscription(self):
        # Test subscribing to a plan when an active subscription already exists
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=1),
        )
        # Ensure the subscription is active
        subscription.activate(self.plan)

        response = self.client.get(
            reverse("subscriptions:subscribe_user", args=[self.plan.id])
        )
        self.assertRedirects(response, reverse("subscriptions:subscription_plans"))

    def test_subscription_success_view(self):
        response = self.client.get(reverse("subscriptions:subscription_success"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "success.html")
