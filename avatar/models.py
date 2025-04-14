from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class AvatarItem(models.Model):
    ITEM_TYPES = (
        ('hat', 'Hat'),
        ('shirt', 'Shirt'),
        ('accessory', 'Accessory'),
        ('background', 'Background'),
    )
    name = models.CharField(max_length=50)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    image = models.ImageField(upload_to='avatar_items/')
    description = models.CharField(max_length=200, blank=True)
    condition = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.item_type})"
    
    def get_condition_text(self):
        condition = self.condition.split("_")
        condition_type, condition_value = condition[0], int(condition[1])

        if condition_type == "total_rides":
            return f"Complete {condition_value} rides"
        elif condition_type == "bike_rides":
            return f"Complete {condition_value} bike rides"
        elif condition_type == "scooter_rides":
            return f"Complete {condition_value} scooter rides"
        elif condition_type == "total_hours":
            return f"Spend {condition_value} hours riding"
        elif condition_type == "total_spent":
            return f"Spend €{condition_value}"
        return "Unknown condition"

class UserAvatar(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    equipped_hat = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_hat', limit_choices_to={'item_type': 'hat'})
    equipped_shirt = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_shirt', limit_choices_to={'item_type': 'shirt'})
    equipped_accessory = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_accessory', limit_choices_to={'item_type': 'accessory'})
    equipped_background = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_background', limit_choices_to={'item_type': 'background'})
    unlocked_items = models.ManyToManyField(AvatarItem, related_name='unlocked_by', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Avatar"