from django.db import models


class Book(models.Model):
    class CoverChoices(models.TextChoices):
        HARD = "hard"
        SOFT = "soft"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=64, choices=CoverChoices.choices)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField()

    class Meta:
        ordering = ["title"]
        unique_together = ("title", "author")

    def __str__(self):
        return self.title
