from django.contrib import admin

from .models import StudentDocument


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "document_type",
        "academic_term",
        "title",
        "version",
        "status",
        "uploaded_by",
        "created_at",
    )

    list_filter = (
        "document_type",
        "status",
        "academic_term",
    )

    search_fields = (
        "student__student_no",
        "student__user__username",
        "title",
    )

    readonly_fields = (
        "created_at",
        "reviewed_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False