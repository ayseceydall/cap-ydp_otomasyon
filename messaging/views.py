
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from auditlog.services import log_action

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
    try:
        form = MessageForm(user=request.user)
        return render(
            request,
            "messaging/message_compose.html",
            {"form": form},
        )
    except Exception:
        logger.exception(
            "Mesaj oluşturma sayfası açılırken hata oluştu. "
            "Kullanıcı ID: %s, Rol: %s",
            request.user.pk,
            getattr(request.user, "role", None),
        )
        raise

    return render(
        request,
        "messaging/message_compose.html",
        {"form": form},
    )


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
    if request.user.role == "chair":
        # Bölüm başkanı mesajları yalnızca görüntüler.
        queryset = Message.objects.all()
    else:
        # Diğer kullanıcılar yalnızca kendi mesajlarını görebilir.
        queryset = (
            Message.objects.filter(recipient=request.user)
            | Message.objects.filter(sender=request.user)
        )

    message = get_object_or_404(
        queryset,
        pk=pk,
    )

    # Bölüm başkanı mesajı açtığında okundu durumu değişmez.
    # Yalnızca mesajın alıcısı okundu durumunu güncelleyebilir.
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
