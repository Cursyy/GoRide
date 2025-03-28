from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Booking
from subscriptions.models import UserSubscription, SubscriptionPlan, UserStatistics
from find_transport.models import Vehicle
from vouchers.models import Voucher

CustomUser = get_user_model()

class BookingTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client.force_login(self.user)
        self.vehicle = Vehicle.objects.create(
            type="E-Scooter",
            price_per_hour=Decimal("5.00"),
            status=True,
            battery_percentage=100,
        )
        self.plan = SubscriptionPlan.objects.create(
            type="Monthly",
            price=Decimal("50.00"),
            duration_days=30,
            max_ride_hours=20
        )
        self.voucher = Voucher.objects.create(
            code="TEST50",
            discount=50,
            active=True,
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
            max_use=10
        )

    def test_rent_vehicle_get(self):
        response = self.client.get(reverse("booking:rent_vehicle", args=[self.vehicle.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rental_booking.html")
        self.assertEqual(response.context["vehicle"], self.vehicle)

    def test_rent_vehicle_unavailable(self):
        self.vehicle.status = False
        self.vehicle.save()
        response = self.client.get(reverse("booking:rent_vehicle", args=[self.vehicle.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("find_transport:find_transport"))

    def test_rent_vehicle_post_stripe(self):
        data = {"hours": "2", "payment_type": "Stripe"}
        response = self.client.post(reverse("booking:rent_vehicle", args=[self.vehicle.id]), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("booking:booking_success"))
        booking = Booking.objects.first()
        self.assertEqual(booking.amount, Decimal("10.00"))
        self.assertEqual(booking.payment_type, "Stripe")
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.status)

    def test_rent_vehicle_with_voucher(self):
        data = {"hours": "2", "payment_type": "Stripe", "voucher_code": "TEST50"}
        response = self.client.post(reverse("booking:rent_vehicle", args=[self.vehicle.id]), data)
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.first()
        self.assertEqual(booking.amount, Decimal("5.00"))
        self.assertEqual(booking.voucher, "TEST50")
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.used, 1)

    def test_rent_vehicle_with_subscription(self):
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            remaining_rides=10,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        data = {"hours": "2", "payment_type": "Subscription"}
        response = self.client.post(reverse("booking:rent_vehicle", args=[self.vehicle.id]), data)
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.first()
        self.assertEqual(booking.amount, Decimal("0.00"))
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.remaining_rides, 6)

    def test_subscribe_get(self):
        response = self.client.get(reverse("booking:subscribe", args=[self.plan.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subscription_booking.html")
        self.assertEqual(response.context["plan"], self.plan)

    def test_subscribe_post(self):
        data = {"payment_type": "Stripe"}
        response = self.client.post(reverse("booking:subscribe", args=[self.plan.id]), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("subscriptions:subscription_success"))
        booking = Booking.objects.first()
        self.assertEqual(booking.amount, self.plan.price)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertTrue(subscription.is_active())

    def test_booking_success(self):
        response = self.client.get(reverse("booking:booking_success"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "booking_success.html")