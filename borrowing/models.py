from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, F

from book.models import Book


FINE_MULTIPLIER = 2


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

    @property
    def price(self):
        return self.book.daily_fee * (
            (self.expected_return_date - self.borrow_date).days + 1
        )

    @property
    def overdue(self):
        if (
            self.actual_return_date
            and self.actual_return_date > self.expected_return_date
        ):
            return (
                (self.actual_return_date - self.expected_return_date).days
                * self.book.daily_fee
                * FINE_MULTIPLIER
            )
        return 0
