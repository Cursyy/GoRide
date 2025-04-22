from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from stats.models import UserStatistics

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_statistics(sender, instance, created, **kwargs):
    if created:
        UserStatistics.objects.create(user=instance)
