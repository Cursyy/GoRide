from django.urls import path
from .views import user_chat_view, admin_chat, admin_chats

app_name = "support"

urlpatterns = [
    path("chat/", user_chat_view, name="user_chat_no_id"),
    path("chat/<int:chat_id>/", user_chat_view, name="user_chat"),
    path("admin-chats/<uuid:chat_id>/", admin_chat, name="admin_chat"),
    path("admin-chats/", admin_chats, name="admin_chat_list"),
]
