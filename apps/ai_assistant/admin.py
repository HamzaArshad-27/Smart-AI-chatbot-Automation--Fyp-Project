from django.contrib import admin

from .models import ChatHistory, UserProductInterest


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "short_message", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "message", "response")
    readonly_fields = ("created_at",)

    def short_message(self, obj):
        return obj.message[:80]


@admin.register(UserProductInterest)
class UserProductInterestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "interest_type", "weight", "created_at")
    list_filter = ("interest_type", "created_at")
    search_fields = ("user__email", "product__name")
    readonly_fields = ("created_at",)
