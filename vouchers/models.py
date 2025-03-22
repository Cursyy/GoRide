from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Voucher(models.Model):
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    discount = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    active = models.BooleanField()
    user = models.ForeignKey(
        "accounts.CustomUser", on_delete=models.CASCADE, null=True, blank=True
    )
    voucher_type = models.CharField(max_length=50, null=True, blank=True)
    max_use = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        null=True,
        blank=True,
    )
    used = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.code
