from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Chat, Message
from .forms import MessageForm
from django.http import JsonResponse


# View for user to interact with their chat
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
            return redirect("support:user_chat")
    else:
        form = MessageForm()

    messages = Message.objects.filter(chat=chat).order_by("created_at")
    return render(
        request,
        "support/user_chat.html",
        {"chat": chat, "form": form, "messages": messages},
    )


@login_required
def user_chat_unread(request):
    unread_message = Message.objects.filter(
        receiver=request.user, is_read=False
    ).count()
    return JsonResponse({"new messages": unread_message}, safe=False)
