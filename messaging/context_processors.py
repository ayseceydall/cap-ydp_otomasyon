
from .models import Message


def unread_message_count(request):
    if not request.user.is_authenticated:
        return {"unread_message_count": 0}

    if getattr(request.user, "role", None) == "chair":
        return {"unread_message_count": 0}

    count = Message.objects.filter(
        recipient=request.user,
        read_at__isnull=True,
    ).count()

    return {"unread_message_count": count}
