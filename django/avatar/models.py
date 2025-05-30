from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from stats.models import UserStatistics
from django.utils.translation import gettext_lazy as _

class AvatarItem(models.Model):
    ITEM_TYPES = (
        ('hat', 'Hat'),
        ('shirt', 'Shirt'),
        ('accessory', 'Accessory'),
        ('background', 'Background'),
    )
    name = models.CharField(max_length=50)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    image = models.ImageField(upload_to='avatar_items/', blank=True)
    preview_image = models.ImageField(upload_to='avatar_items/preview/', blank=True, null=True)
    description = models.CharField(max_length=200, blank=True)
    condition = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.item_type})"
    
    def get_condition_text(self):
        if not self.condition or "__" not in self.condition:
            return "Unknown condition"

        condition = self.condition.split("__")

        if len(condition) != 2:
            return "Invalid condition format"

        try:
            condition_type, condition_value = condition[0], int(condition[1])
        except (IndexError, ValueError):
            return "Invalid condition value"

        if condition_type == "total_rides":
            return _("Complete %(value)s rides") % {'value': condition_value}
        elif condition_type == "bike_rides":
            return _("Complete %(value)s bike rides") % {'value': condition_value}
        elif condition_type == "scooter_rides":
            return _("Complete %(value)s scooter rides") % {'value': condition_value}
        elif condition_type == "total_hours":
            return _("Spend %(value)s hours riding") % {'value': condition_value}
        elif condition_type == "total_spent":
            return _("Spend €%(value)s") % {'value': condition_value}
        return _("Unknown condition")


class UserAvatar(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    equipped_hat = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_hat', limit_choices_to={'item_type': 'hat'})
    equipped_shirt = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_shirt', limit_choices_to={'item_type': 'shirt'})
    equipped_accessory = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_accessory', limit_choices_to={'item_type': 'accessory'})
    equipped_background = models.ForeignKey(AvatarItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_background', limit_choices_to={'item_type': 'background'})
    unlocked_items = models.ManyToManyField(AvatarItem, related_name='unlocked_by', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Avatar"
    
    def check_and_unlock_items(self):
        old_items = set(self.unlocked_items.values_list('id', flat=True))

        try:
            stats = UserStatistics.objects.get(user=self.user)
        except UserStatistics.DoesNotExist:
            stats, _ = UserStatistics.objects.get_or_create(user=self.user)

        all_items = AvatarItem.objects.all()

        for item in all_items:
            if item in self.unlocked_items.all():
                continue

            condition = item.condition.split("__")
            if len(condition) != 2:
                print(f"Invalid condition format for item {item.name}")
                continue 

            condition_type, condition_value = condition[0], int(condition[1])
            condition_met = False

            if condition_type == "total_rides" and stats.total_rides >= condition_value:
                condition_met = True
            elif condition_type == "bike_rides" and stats.bike_rides >= condition_value:
                condition_met = True
            elif condition_type == "scooter_rides" and stats.scooter_rides >= condition_value:
                condition_met = True
            elif condition_type == "total_hours" and stats.total_hours >= condition_value:
                condition_met = True
            elif condition_type == "total_spent" and stats.total_spent >= condition_value:
                condition_met = True

            if condition_met:
                self.unlocked_items.add(item)

        self.save()

        new_items = set(self.unlocked_items.values_list('id', flat=True)) - old_items
        return AvatarItem.objects.filter(id__in=new_items)