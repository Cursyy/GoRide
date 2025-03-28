from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Route(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="routes")
    name = models.CharField(max_length=255) 
    points = models.JSONField() 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
