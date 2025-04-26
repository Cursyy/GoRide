from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Chat, Message
from .forms import MessageForm
from django.shortcuts import get_object_or_404


@login_required
def user_chat_view(request, chat_id=None):
    chat = (
        get_object_or_404(Chat, id=chat_id)
        if chat_id
        else Chat.objects.get_or_create(user=request.user, is_active=True)[0]
    )
    chat.agent = request.user
    chat.save()
    if not request.user.is_staff and chat.user != request.user:
        return redirect("support:user_chat")
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.receiver = chat.agent
            message.save()

            return redirect("support:user_chat", chat_id=chat.id)
    else:
        form = MessageForm()

    messages = Message.objects.filter(chat=chat).order_by("created_at")
    return render(
        request,
        "support/user_chat.html",
        {"chat": chat, "form": form, "messages": messages},
    )


@login_required
def admin_chat(request, chat_id=None):
    if not request.user.is_staff:
        return redirect("support:user_chat")

    chat = get_object_or_404(Chat, id=chat_id) if chat_id else None
    active_chats = Chat.objects.filter(is_active=True)
    chat.agent = request.user
    chat.save()
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid() and chat:
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.receiver = chat.agent
            message.save()

            form = MessageForm()

    else:
        form = MessageForm()

    messages = Message.objects.filter(chat=chat).order_by("created_at") if chat else []
    return render(
        request,
        "support/admin_chat.html",
        {"chats": active_chats, "chat": chat, "form": form, "messages": messages},
    )


@login_required
def admin_chats(request):
    if not request.user.is_staff:
        return redirect("support:user_chat")
    Chat.objects.filter(is_active=True)
    return render(
        request,
        "support/admin_chats.html",
        {"chats": Chat.objects.filter(is_active=True)},
    )
