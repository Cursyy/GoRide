from django.db import models
from django.contrib.auth.models import AbstractBaseUser

class CustomUser(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=32)
    is_admin = models.BooleanField(default=False)
    phone_num = models.CharField(max_length=15)
    profile_pic = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    groups = models.ManyToManyField("auth.Group", blank=True, related_name="Customer")
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
