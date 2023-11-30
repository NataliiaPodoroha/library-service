from django.db import models

from borrowing.models import Borrowing


class Payment(models.Model):
    STATUSES = (
        ("PENDING", "Pending"),
        ("PAID", "Paid")
    )
    TYPES = (
        ("PAYMENT", "Payment"),
        ("FINE", "Fine")
    )
    status = models.CharField(
        max_length=7, choices=STATUSES, default="PENDING"
    )
    type = models.CharField(
        max_length=7, choices=TYPES, default="PAYMENT"
    )
    borrowing = models.ForeignKey(
        to=Borrowing,
        related_name="payments",
        on_delete=models.CASCADE,
    )
    session_url = models.URLField(max_length=511)
    session_id = models.CharField(max_length=255, unique=True)
    money_to_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
