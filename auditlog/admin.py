
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor",
        "action",
        "model_label",
        "object_id",
        "summary",
    )

    list_filter = (
        "action",
        "model_label",
        "created_at",
    )

    search_fields = (
        "actor__username",
        "model_label",
        "object_id",
        "summary",
        "reason",
    )

    readonly_fields = tuple(
        field.name for field in AuditLog._meta.fields
    )

    date_hierarchy = "created_at"
    list_select_related = ("actor",)

    def _can_view_audit_logs(self, request):
        user = request.user
        return (
            user.is_active
            and user.is_staff
            and (
                user.is_superuser
                or getattr(user, "role", None)
                in {"coordinator", "chair"}
            )
        )

    def has_module_permission(self, request):
        return self._can_view_audit_logs(request)

    def has_view_permission(self, request, obj=None):
        return self._can_view_audit_logs(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
