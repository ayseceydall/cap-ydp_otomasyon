from django.contrib import admin

from .models import (
    Course,
    AcademicTerm,
    StudentRequiredCourse,
    CourseAttempt,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "course_code",
        "course_name",
        "credit",
        "ects",
        "is_active",
    )

    search_fields = ("course_code", "course_name")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = (
        "academic_year",
        "term",
        "starts_on",
        "ends_on",
        "is_current",
    )

    list_filter = ("academic_year", "term", "is_current")
    readonly_fields = ("created_at",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StudentRequiredCourse)
class StudentRequiredCourseAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "status",
        "added_at",
        "added_by",
    )

    list_filter = ("status",)
    search_fields = (
        "student__student_no",
        "course__course_code",
        "course__course_name",
    )

    readonly_fields = (
        "added_at",
        "removed_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CourseAttempt)
class CourseAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "term",
        "passed_term",
        "grade",
        "academic_status",
        "approval_status",
        "is_historical",
    )

    list_filter = (
        "academic_status",
        "approval_status",
        "is_historical",
        "term",
    )

    search_fields = (
        "student__student_no",
        "course__course_code",
        "course__course_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False