from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
import json

from .models import Route

User = get_user_model()

class RouteModelTest(TestCase):
    def setUp(self):
        """Create a test user for route creation"""
        self.user = User.objects.create_user(
            username='testuser', 
            password='12345',
            email ='test@test.test'
        )

    def test_route_creation(self):
        """Test creating a route"""
        route = Route.objects.create(
            user=self.user,
            name='Test Route',
            points=[
                {"lat": 53.349805, "lon": -6.26031},
                {"lat": 53.350805, "lon": -6.27031}
            ]
        )
        
        self.assertIsNotNone(route.id)
        self.assertEqual(route.name, 'Test Route')
        self.assertEqual(route.user, self.user)
        self.assertIsNotNone(route.created_at)

    def test_route_string_representation(self):
        """Test the string representation of a route"""
        route = Route.objects.create(
            user=self.user,
            name='Test Route',
            points=[]
        )
        
        self.assertEqual(str(route), 'Test Route')

class GetPlacesViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('requests.get')
    def test_get_places_success(self, mock_get):
        """Test successful places retrieval"""
        # Mock successful API response
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "name": "Test Place",
                        "category": "restaurant"
                    }
                }
            ]
        }

        url = reverse('get_direction:get_places', 
                      kwargs={
                          'category': 'restaurant', 
                          'lat': '53.349805', 
                          'lon': '-6.26031'
                      })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('features', response.json())

    @patch('requests.get')
    def test_get_places_api_failure(self, mock_get):
        """Test API failure scenario"""
        # Mock API failure
        mock_response = mock_get.return_value
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        url = reverse('get_direction:get_places', 
                      kwargs={
                          'category': 'restaurant', 
                          'lat': '53.349805', 
                          'lon': '-6.26031'
                      })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class GetRouteViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('requests.get')
    def test_get_route_success(self, mock_get):
        """Test successful route retrieval"""
        # Mock successful API response
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "distance": 1000,
                        "time": 300
                    }
                }
            ]
        }

        # Prepare route request data
        route_data = {
            "waypoints": [
                [53.349805, -6.26031],
                [53.350805, -6.27031]
            ]
        }

        url = reverse('get_direction:get_route')
        response = self.client.post(
            url, 
            data=json.dumps(route_data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('features', response.json())

    def test_get_route_invalid_waypoints(self):
        """Test route retrieval with invalid waypoints"""
        url = reverse('get_direction:get_route')
        
        # Test with no waypoints
        response = self.client.post(
            url, 
            data=json.dumps({"waypoints": []}), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test with insufficient waypoints
        response = self.client.post(
            url, 
            data=json.dumps({"waypoints": [[53.349805, -6.26031]]}), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_get_route_method_not_allowed(self):
        """Test GET method is not allowed"""
        url = reverse('get_direction:get_route')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 405)



class MapViewTest(TestCase):
    def test_map_view_renders_correct_template(self):
        """Test map view renders the correct template"""
        url = reverse('get_direction:map')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "get_direction/get_direction.html")