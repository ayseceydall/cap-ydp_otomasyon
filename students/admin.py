from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        "student_no",
        "user",
        "program_type",
        "acceptance_academic_year",
        "acceptance_term",
        "status",
    )

    list_filter = (
        "program_type",
        "acceptance_term",
        "status",
    )

    search_fields = (
        "student_no",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )

    ordering = ("student_no",)