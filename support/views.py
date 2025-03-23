from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Chat, Message
from .forms import MessageForm
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@login_required
def user_chat_view(request):
    chat, created = Chat.objects.get_or_create(user=request.user, is_active=True)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.save()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "support", {"type": "chat_message", "message": message.content}
            )

            return redirect("support:user_chat")
    else:
        form = MessageForm()

    messages = Message.objects.filter(chat=chat).order_by("created_at")
    return render(
        request,
        "support/user_chat.html",
        {"chat": chat, "form": form, "messages": messages},
    )
