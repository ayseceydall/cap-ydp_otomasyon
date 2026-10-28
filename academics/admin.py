from django.contrib import admin

from .models import (
    Course,
    AcademicTerm,
    StudentRequiredCourse,
    CourseAttempt,
    AcademicRuleVersion
)

from auditlog.services import log_action


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


    
@admin.register(AcademicRuleVersion)
class AcademicRuleVersionAdmin(admin.ModelAdmin):
    list_display = (
        "version_code",
        "title",
        "effective_from",
        "effective_to",
        "created_by",
        "created_at",
    )

    list_filter = (
        "effective_from",
        "effective_to",
    )

    search_fields = (
        "version_code",
        "title",
        "notes",
    )

    ordering = ("-effective_from",)
    date_hierarchy = "effective_from"
    actions = None

    def _can_access_rules(self, request):
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
        return self._can_access_rules(request)

    def has_view_permission(self, request, obj=None):
        return self._can_access_rules(request)

    def has_add_permission(self, request):
        user = request.user
        return (
            user.is_active
            and user.is_staff
            and (
                user.is_superuser
                or getattr(user, "role", None) == "coordinator"
            )
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return tuple(
                field.name
                for field in self.model._meta.fields
            )

        return ("created_by", "created_at")

    def save_model(self, request, obj, form, change):
        if change:
            raise PermissionError(
                "Mevcut akademik kural sürümleri değiştirilemez."
            )

        obj.created_by = request.user
        obj.full_clean()

        super().save_model(request, obj, form, change)

        log_action(
            actor=request.user,
            action="CREATE",
            instance=obj,
            summary="Yeni akademik kural sürümü oluşturuldu.",
            new_values={
                "version_code": obj.version_code,
                "title": obj.title,
                "effective_from": str(obj.effective_from),
                "effective_to": (
                    str(obj.effective_to)
                    if obj.effective_to
                    else None
                ),
                "rules": obj.rules,
            },
            request=request,
        )
