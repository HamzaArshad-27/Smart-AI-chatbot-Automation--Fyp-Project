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



class UserChatPreference(models.Model):
    """Track user preferences for personalization"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_preferences')
    category = models.CharField(max_length=100, blank=True, null=True)
    keyword = models.CharField(max_length=200, blank=True, null=True)
    viewed_products = models.ManyToManyField(Product, blank=True, related_name='viewed_by')
    interest_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_chat_preferences'
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'keyword']),
        ]

class UserRecommendation(models.Model):
    """Store product recommendations for users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommended_to')
    reason = models.CharField(max_length=255, blank=True)
    clicked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_recommendations'