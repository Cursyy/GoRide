import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from vouchers.forms import VoucherApplyForm

from .models import Voucher
from find_transport.models import Vehicle
from subscriptions.models import SubscriptionPlan
from accounts.models import CustomUser

User = get_user_model()

class VoucherModelTest(TestCase):
    def setUp(self):
        """Create a test user and a test voucher"""
        self.user = CustomUser.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='12345'
        )

    def test_voucher_creation(self):
        """Test creating a voucher"""
        now = timezone.now()
        voucher = Voucher.objects.create(
            code='TEST100',
            valid_from=now,
            valid_to=now + timedelta(days=30),
            discount=20,
            active=True,
            user=self.user,
            voucher_type='vehicle',
            max_use=5,
            used=0
        )
        
        self.assertIsNotNone(voucher.id)
        self.assertEqual(voucher.code, 'TEST100')
        self.assertEqual(voucher.discount, 20)
        self.assertTrue(voucher.active)
        self.assertEqual(voucher.user, self.user)

    def test_voucher_string_representation(self):
        """Test the string representation of a voucher"""
        voucher = Voucher.objects.create(
            code='TEST100',
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            discount=20,
            active=True
        )
        
        self.assertEqual(str(voucher), 'TEST100')

class VoucherApplyViewTest(TestCase):
    def setUp(self):
        """Set up test data for voucher application"""
        self.client = Client()
        
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='12345'
        )

        # Create a test vehicle
        self.vehicle = Vehicle.objects.create(
            type='E-Bike',
            latitude=53.349805,
            longitude=-6.26031,
            status=True,
            battery_percentage=80,
            price_per_hour=10.0
        )

        # Create a test subscription plan
        self.subscription_plan = SubscriptionPlan.objects.create(
            type='Weekly',
            price=50.0,
        )

        # Create a valid vehicle voucher
        self.vehicle_voucher = Voucher.objects.create(
            code='VEHICLE20',
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            discount=20,
            active=True,
            voucher_type='vehicle',
            max_use=5,
            used=0
        )

        # Create a valid subscription voucher
        self.subscription_voucher = Voucher.objects.create(
            code='SUB10',
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            discount=10,
            active=True,
            voucher_type='subscription',
            max_use=5,
            used=0
        )

    def test_vehicle_voucher_application(self):
        """Test applying a voucher to a vehicle rental"""
        url = reverse('vouchers:voucher_apply')
        
        data = {
            'vehicle_id': self.vehicle.id,
            'code': 'VEHICLE20',
            'type': 'vehicle'
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Original price is 10.0, with 20% discount it should be 8.0
        self.assertAlmostEqual(result['price'], 8.0)
        self.assertEqual(result['discount'], 20)

    def test_subscription_voucher_application(self):
        """Test applying a voucher to a subscription"""
        url = reverse('vouchers:voucher_apply')
        
        data = {
            'subscription': self.subscription_plan.id,
            'code': 'SUB10',
            'type': 'subscription'
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Original price is 50.0, with 10% discount it should be 45.0
        self.assertAlmostEqual(float(result['price']), 45.0)
        self.assertEqual(result['discount'], 10)

    def test_invalid_voucher_code(self):
        """Test applying an invalid voucher code"""
        url = reverse('vouchers:voucher_apply')
        
        data = {
            'vehicle_id': self.vehicle.id,
            'code': 'INVALID_CODE',
            'type': 'vehicle'
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid voucher code', response.json()['error'])

    def test_expired_voucher(self):
        """Test applying an expired voucher"""
        # Create an expired voucher
        expired_voucher = Voucher.objects.create(
            code='EXPIRED20',
            valid_from=timezone.now() - timedelta(days=60),
            valid_to=timezone.now() - timedelta(days=30),
            discount=20,
            active=True,
            voucher_type='vehicle',
            max_use=5,
            used=0
        )
        
        url = reverse('vouchers:voucher_apply')
        
        data = {
            'vehicle_id': self.vehicle.id,
            'code': 'EXPIRED20',
            'type': 'vehicle'
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)

    def test_inactive_voucher(self):
        """Test applying an inactive voucher"""
        # Create an inactive voucher
        inactive_voucher = Voucher.objects.create(
            code='INACTIVE20',
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            discount=20,
            active=False,
            voucher_type='vehicle',
            max_use=5,
            used=0
        )
        
        url = reverse('vouchers:voucher_apply')
        
        data = {
            'vehicle_id': self.vehicle.id,
            'code': 'INACTIVE20',
            'type': 'vehicle'
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid voucher code', response.json()['error'])

    def test_voucher_usage_limit(self):
        """Test applying a voucher that has reached its usage limit"""
        # Create a voucher with max uses reached
        max_used_voucher = Voucher.objects.create(
            code='MAXUSED20',
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=30),
            discount=20,
            active=True,
            voucher_type='vehicle',
            max_use=1,
            used=1
        )
        
        url = reverse('vouchers:voucher_apply')
        
        data = {
            'vehicle_id': self.vehicle.id,
            'code': 'MAXUSED20',
            'type': 'vehicle'
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('usage limit reached', response.json()['error'])

class VoucherApplyFormTest(TestCase):
    def test_voucher_apply_form_valid(self):
        """Test the voucher apply form with a valid code"""
        form_data = {'code': 'TESTCODE'}
        form = VoucherApplyForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_voucher_apply_form_invalid(self):
        """Test the voucher apply form with an empty code"""
        form_data = {'code': ''}
        form = VoucherApplyForm(data=form_data)
        self.assertFalse(form.is_valid())