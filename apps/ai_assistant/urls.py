from django.urls import path

from apps.ai_assistant import views

app_name = "ai_assistant"

urlpatterns = [
    path("chat/", views.chat_api, name="chat"),
    path("interest/", views.track_interest_api, name="track_interest"),
]
