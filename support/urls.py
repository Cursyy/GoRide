from django.urls import path
from .views import user_chat_view, user_chat_unread

app_name = "support"

urlpatterns = [
    path("chat/", user_chat_view, name="user_chat"),
    path("chat/unread/", user_chat_unread, name="user_chat_unread"),
]
