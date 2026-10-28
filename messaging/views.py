
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from auditlog.services import log_action

from .forms import MessageForm
from .models import Message


@login_required(login_url="/giris/")
def message_compose(request):
    if getattr(request.user, "role", None) not in {
        "student",
        "coordinator",
        "chair",
    }:
        raise PermissionDenied

    if request.method == "POST":
        form = MessageForm(request.POST, user=request.user)

        if form.is_valid():
            with transaction.atomic():
                message = form.save(commit=False)
                message.sender = request.user
                message.full_clean()
                message.save()

                log_action(
                    actor=request.user,
                    action="CREATE",
                    instance=message,
                    summary="Yeni mesaj gönderildi.",
                    new_values={
                        "recipient": message.recipient.username,
                        "subject": message.subject,
                    },
                    request=request,
                )

            messages.success(request, "Mesajın gönderildi.")
            return redirect("message_sent")

    else:
        form = MessageForm(user=request.user)

    return render(
        request,
        "messaging/message_compose.html",
        {"form": form},
    )


@login_required(login_url="/giris/")
def message_inbox(request):
    received_messages = (
        Message.objects.filter(recipient=request.user)
        .select_related("sender")
        .order_by("-created_at")
    )

    return render(
        request,
        "messaging/message_inbox.html",
        {"messages_list": received_messages},
    )


@login_required(login_url="/giris/")
def message_sent(request):
    sent_messages = (
        Message.objects.filter(sender=request.user)
        .select_related("recipient")
        .order_by("-created_at")
    )

    return render(
        request,
        "messaging/message_sent.html",
        {"messages_list": sent_messages},
    )


@login_required(login_url="/giris/")
def message_detail(request, pk):
    message = get_object_or_404(
        Message.objects.filter(
            recipient=request.user
        ) | Message.objects.filter(
            sender=request.user
        ),
        pk=pk,
    )

    if (
        message.recipient_id == request.user.pk
        and message.read_at is None
    ):
        from django.utils import timezone

        message.read_at = timezone.now()
        message.save(update_fields=["read_at"])

    return render(
        request,
        "messaging/message_detail.html",
        {"message": message},
    )
