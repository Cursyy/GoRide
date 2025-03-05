from django.test import TestCase
from django.urls import reverse
from .models import Vehicle


class FindTransportViewTest(TestCase):
    def setUp(self):
        self.bike = Vehicle.objects.create(
            type="Bike",
            latitude=53.349805,
            longitude=-6.26031,
            status=True,
            price_per_hour=2.5,
        )
        self.e_bike = Vehicle.objects.create(
            type="E-Bike",
            latitude=53.349805,
            longitude=-6.26031,
            status=True,
            battery_percentage=80,
            price_per_hour=5.0,
        )
        self.e_scooter = Vehicle.objects.create(
            type="E-Scooter",
            latitude=53.349805,
            longitude=-6.26031,
            status=True,
            battery_percentage=50,
            price_per_hour=3.0,
        )
        self.unavailable_e_bike = Vehicle.objects.create(
            type="E-Bike",
            latitude=53.349805,
            longitude=-6.26031,
            status=False,
            battery_percentage=60,
            price_per_hour=4.0,
        )

    def test_find_transport_view(self):
        response = self.client.get(reverse("find_transport:find_transport"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-Bike")
        self.assertContains(response, "E-Scooter")
        self.assertContains(response, "Bike")
        self.assertNotContains(response, "Not Available")

    def test_find_transport_view_with_type_filter(self):
        response = self.client.get(
            reverse("find_transport:find_transport"), {"type": "E-Bike"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-Bike")
        self.assertNotContains(response, "Bike")
        self.assertNotContains(response, "E-Scooter")

    def test_find_transport_view_with_min_battery_filter(self):
        response = self.client.get(
            reverse("find_transport:find_transport"), {"min_battery": "70"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-Bike")
        self.assertNotContains(response, "E-Scooter")

    def test_find_transport_view_with_both_filters(self):
        response = self.client.get(
            reverse("find_transport:find_transport"),
            {"type": "E-Scooter", "min_battery": "70"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "E-Scooter")

    def test_find_transport_invalid_battery(self):
        response = self.client.get(
            reverse("find_transport:find_transport"), {"min_battery": "abc"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"error": "Invalid battery percentage"})
