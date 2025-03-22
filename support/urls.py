from django.urls import path
from .views import user_chat_view

app_name = "support"

urlpatterns = [
    path("chat/", user_chat_view, name="user_chat"),
]
