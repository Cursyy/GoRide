from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import Booking
from subscriptions.models import UserSubscription, SubscriptionPlan
from find_transport.models import Vehicle
from vouchers.models import Voucher
from decimal import Decimal
from django.utils import timezone


class BookingViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@gmail.com",
            password="password",
            is_active=True,
        )
        self.client.force_login(self.user)
        self.vehicle = Vehicle.objects.create(
            id=1,
            type="Bike",
            price_per_hour=10,
            status=True,
            latitude=0.0,
            longitude=0.0,
        )
        self.plan = SubscriptionPlan.objects.create(
            id=1, type="Weekly", price=100, duration_days=30
        )
        self.voucher = Voucher.objects.create(
            code="DISCOUNT10",
            discount=10,
            valid_from=timezone.now(),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            active=True,
        )

    def test_rent_vehicle_get(self):
        response = self.client.get(reverse("booking:rent_vehicle", args=[self.vehicle.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rental_booking.html")

    def test_rent_vehicle_post_without_subscription(self):
        response = self.client.post(
            reverse("booking:rent_vehicle", args=[self.vehicle.id]),
            {"hours": 2, "payment_type": "Stripe"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.amount, Decimal("20.00"))
        self.assertEqual(booking.status, "Paid")
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.status)

    def test_rent_vehicle_post_with_voucher(self):
        response = self.client.post(
            reverse("booking:rent_vehicle", args=[self.vehicle.id]),
            {"hours": 2, "payment_type": "Stripe", "voucher_code": self.voucher.code},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.amount, Decimal("18.00"))
        self.assertEqual(booking.status, "Paid")
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.status)

    def test_subscribe_get(self):
        response = self.client.get(reverse("booking:subscribe_plan", args=[self.plan.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subscription_booking.html")

    def test_subscribe_post(self):
        response = self.client.post(
            reverse("booking:subscribe_plan", args=[self.plan.id]),
            {"payment_type": "Stripe"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.amount, Decimal("100.00"))
        self.assertEqual(booking.status, "Paid")
        self.assertTrue(UserSubscription.objects.filter(user=self.user).exists())

    @patch("successful_booking.send_transaction_email")
    def test_rent_vehicle_sends_email(self, mock_send_email):
        self.client.post(
            reverse("booking:rent_vehicle", args=[self.vehicle.id]),
            {"hours": 2, "payment_type": "Stripe"},
        )
        self.assertTrue(mock_send_email.called)

    @patch("successful_booking.send_transaction_email")
    def test_subscribe_sends_email(self, mock_send_email):
        self.client.post(
            reverse("booking:subscribe_plan", args=[self.plan.id]),
            {"payment_type": "Stripe"},
        )
        self.assertTrue(mock_send_email.called)
