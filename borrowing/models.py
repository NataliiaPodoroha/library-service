from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, F

from book.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowings"
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="borrowings"
    )

    class Meta:
        ordering = ["-borrow_date"]
        constraints = [
            models.CheckConstraint(
                check=Q(expected_return_date__gte=F("borrow_date"))
                & Q(actual_return_date__gte=F("borrow_date")),
                name="valid_return_date",
            )
        ]
