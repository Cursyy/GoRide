from django.contrib import admin
from .models import Chat, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 1


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "is_active")
    search_fields = ("user__username",)
    inlines = [MessageInline]
    list_filter = ("is_active",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "content", "created_at", "chat")
    search_fields = ("content", "sender__username", "chat__user__username")
