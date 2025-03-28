from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Vehicle, EVStation

class VehicleModelTest(TestCase):
    def setUp(self):
        self.ev_station = EVStation.objects.create(
            latitude=53.349805,
            longitude=-6.26031,
            max_spaces=5
        )

    def test_bike_creation(self):
        """Test creating a regular Bike without battery percentage"""
        bike = Vehicle.objects.create(
            type="Bike",
            latitude=53.349805,
            longitude=-6.26031,
            status=True,
            price_per_hour=2.5,
        )
        self.assertEqual(bike.battery_percentage, None)
        self.assertEqual(bike.type, "Bike")

    def test_e_bike_creation(self):
        """Test creating an E-Bike with battery percentage"""
        e_bike = Vehicle.objects.create(
            type="E-Bike",
            latitude=53.349805,
            longitude=-6.26031,
            status=True,
            battery_percentage=80,
            price_per_hour=5.0,
            station=self.ev_station
        )
        self.assertEqual(e_bike.battery_percentage, 80)
        self.assertEqual(e_bike.type, "E-Bike")

    def test_e_bike_invalid_battery_percentage(self):
        """Test validation for battery percentage"""
        with self.assertRaises(ValidationError):
            Vehicle.objects.create(
                type="E-Bike",
                latitude=53.349805,
                longitude=-6.26031,
                status=True,
                battery_percentage=101,  # Invalid percentage
                price_per_hour=5.0
            )

    def test_station_capacity(self):
        """Test station capacity limit"""
        # Fill the station to max capacity
        for i in range(5):
            Vehicle.objects.create(
                type="E-Bike",
                latitude=53.349805,
                longitude=-6.26031,
                status=True,
                battery_percentage=80,
                price_per_hour=5.0,
                station=self.ev_station
            )

        # Try to add one more vehicle should raise ValidationError
        with self.assertRaises(ValidationError):
            Vehicle.objects.create(
                type="E-Bike",
                latitude=53.349805,
                longitude=-6.26031,
                status=True,
                battery_percentage=80,
                price_per_hour=5.0,
                station=self.ev_station
            )

class EVStationModelTest(TestCase):
    def test_ev_station_creation(self):
        """Test creating an EV Station"""
        station = EVStation.objects.create(
            latitude=53.349805,
            longitude=-6.26031,
            max_spaces=10
        )
        self.assertIsNotNone(station.id)
        self.assertEqual(station.latitude, 53.349805)
        self.assertEqual(station.longitude, -6.26031)
        self.assertEqual(station.max_spaces, 10)

class GetVehiclesViewTest(TestCase):
    def setUp(self):
        """Set up test data for vehicle filtering"""
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

    def test_get_vehicles_all(self):
        """Test retrieving all available vehicles"""
        response = self.client.get(reverse('find_transport:get_vehicles'))
        self.assertEqual(response.status_code, 200)
        vehicles = response.json()
        self.assertEqual(len(vehicles), 3)  # Only available vehicles

    def test_get_vehicles_by_type(self):
        """Test filtering vehicles by type"""
        response = self.client.get(reverse('find_transport:get_vehicles'), {'type': 'E-Bike'})
        self.assertEqual(response.status_code, 200)
        vehicles = response.json()
        self.assertEqual(len(vehicles), 1)
        self.assertEqual(vehicles[0]['type'], 'E-Bike')

    def test_get_vehicles_by_min_battery(self):
        """Test filtering vehicles by minimum battery percentage"""
        response = self.client.get(reverse('find_transport:get_vehicles'), {'min_battery': '70'})
        self.assertEqual(response.status_code, 200)
        vehicles = response.json()
        self.assertEqual(len(vehicles), 1)
        self.assertEqual(vehicles[0]['battery_percentage'], 80)

    def test_get_vehicles_invalid_battery(self):
        """Test invalid battery percentage input"""
        response = self.client.get(reverse('find_transport:get_vehicles'), {'min_battery': 'abc'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Invalid battery percentage"})

class GetStationViewTest(TestCase):
    def setUp(self):
        """Set up test data for stations"""
        self.station = EVStation.objects.create(
            latitude=53.349805,
            longitude=-6.26031,
            max_spaces=5
        )
        # Create some vehicles at the station
        Vehicle.objects.create(
            type="E-Bike",
            latitude=53.349805,
            longitude=-6.26031,
            status=True,
            battery_percentage=80,
            price_per_hour=5.0,
            station=self.station
        )

    def test_get_stations(self):
        """Test retrieving all stations"""
        response = self.client.get(reverse('find_transport:get_station'))
        self.assertEqual(response.status_code, 200)
        stations = response.json()
        self.assertTrue(len(stations) > 0)

    def test_get_station_invalid_id(self):
        """Test retrieving station with invalid ID"""
        response = self.client.get(f"{reverse('find_transport:get_station')}?id=abc")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Invalid ID"})