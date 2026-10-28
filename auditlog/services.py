
from .models import AuditLog


def log_action(
    *,
    actor,
    action,
    instance,
    summary,
    old_values=None,
    new_values=None,
    reason="",
    request=None,
):
    """
    Sistemde yapılan önemli işlemleri kayıt altına alır.
    Parola veya gizli anahtar gibi hassas veriler gönderilmemelidir.
    """

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        model_label=instance._meta.label,
        object_id=str(instance.pk),
        summary=summary,
        old_values=old_values or {},
        new_values=new_values or {},
        reason=reason,
        request_path=request.path if request else "",
    )
