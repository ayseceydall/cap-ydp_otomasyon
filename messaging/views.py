
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.http import FileResponse, Http404
from django.db.models import Q

from auditlog.services import log_action
import os

from .forms import MessageForm
from .models import Message
import logging

logger = logging.getLogger(__name__)



@login_required(login_url="/giris/")
def message_compose(request):
    if getattr(request.user, "role", None) not in {
        "student",
        "coordinator",
    }:
        raise PermissionDenied

    try:
        if request.method == "POST":
            form = MessageForm(
                request.POST,
                request.FILES,
                user=request.user,
            )

            if form.is_valid():
                with transaction.atomic():
                    message = form.save(commit=False)
                    message.sender = request.user

                    uploaded_attachment = (
                        form.cleaned_data.get("attachment")
                    )

                    if uploaded_attachment:
                        message.attachment_original_name = (
                            os.path.basename(
                                uploaded_attachment.name
                            )[:255]
                        )

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
                            "has_attachment": bool(
                                message.attachment
                            ),
                            "attachment_name": (
                                message.attachment_original_name
                            ),
                        },
                        request=request,
                    )

                messages.success(
                    request,
                    "Mesajın gönderildi.",
                )
                return redirect("message_sent")

        else:
            form = MessageForm(user=request.user)

        return render(
            request,
            "messaging/message_compose.html",
            {"form": form},
        )

    except Exception:
        logger.exception(
            "MESSAGE_COMPOSE_ERROR: "
            "user_id=%s, role=%s, method=%s",
            request.user.pk,
            getattr(request.user, "role", None),
            request.method,
        )
        raise



@login_required(login_url="/giris/")
def message_inbox(request):
    if request.user.role == "chair":
        # Bölüm başkanı mesaj arşivini yalnızca görüntüler.
        messages_list = (
            Message.objects
            .select_related("sender", "recipient")
            .order_by("-created_at")
        )
    else:
        # Öğrenci ve koordinatör yalnızca kendilerine
        # gönderilen mesajları görür.
        messages_list = (
            Message.objects
            .filter(recipient=request.user)
            .select_related("sender")
            .order_by("-created_at")
        )

    return render(
        request,
        "messaging/message_inbox.html",
        {"messages_list": messages_list},
    )



@login_required(login_url="/giris/")
def message_sent(request):
    # Bölüm başkanı gönderilen mesajlar sayfasına erişemez.
    if request.user.role == "chair":
        raise PermissionDenied

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
    try:
        if request.user.role == "chair":
            queryset = Message.objects.all()
        else:
            queryset = (
                Message.objects.filter(recipient=request.user)
                | Message.objects.filter(sender=request.user)
            )

        message = get_object_or_404(
            queryset,
            pk=pk,
        )

        if (
            request.user.role != "chair"
            and message.recipient_id == request.user.pk
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

    except Exception:
        logger.exception(
            "MESSAGE_DETAIL_ERROR: "
            "user_id=%s, role=%s, message_id=%s",
            request.user.pk,
            getattr(request.user, "role", None),
            pk,
        )
        raise



@login_required(login_url="/giris/")
def message_attachment_download(request, pk):
    # Bölüm başkanı yalnızca görüntüleme yapabilir.
    # Mesajın tarafları kendi mesajlarının eklerini indirebilir.
    if getattr(request.user, "role", None) == "chair":
        queryset = Message.objects.all()
    else:
        queryset = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        )

    message = get_object_or_404(queryset, pk=pk)

    if not message.attachment:
        raise Http404("Bu mesajda indirilecek ek bulunamadı.")

    try:
        file_handle = message.attachment.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("Ek dosya bulunamadı.")

    filename = os.path.basename(
        message.attachment_original_name
        or message.attachment.name
    )

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=filename,
    )
