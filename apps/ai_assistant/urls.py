from django.urls import path

from apps.ai_assistant import views

app_name = "ai_assistant"

urlpatterns = [
    path("chat/", views.chat_api, name="chat"),
    path("interest/", views.track_interest_api, name="track_interest"),
    path("data/refresh/", views.refresh_data_api, name="refresh_data"),  # For manual refresh
    path("data/stats/", views.get_stats_api, name="get_stats"),  # Get website stats
]
