from django.conf import settings
from django.db import models

from apps.products.models import Product


class ChatHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_chat_history",
    )
    message = models.TextField()
    response = models.TextField()
    context_used = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_chat_history"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.created_at:%Y-%m-%d %H:%M}"


class UserProductInterest(models.Model):
    INTEREST_CHOICES = [
        ("view", "View"),
        ("like", "Like"),
        ("dislike", "Dislike"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_interests",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="user_interests",
    )
    interest_type = models.CharField(max_length=10, choices=INTEREST_CHOICES)
    weight = models.FloatField(default=1.0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_product_interests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "interest_type"]),
            models.Index(fields=["product", "interest_type"]),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.product_id} ({self.interest_type})"
