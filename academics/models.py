from django.db import models
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q

from config import settings
from students.models import StudentProfile


class Course(models.Model):

    course_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Ders kodu",
    )

    course_name = models.CharField(
        max_length=200,
        verbose_name="Ders adı",
    )

    credit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Kredi",
    )

    ects = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="AKTS",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Açıklama",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif mi?",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturulma tarihi",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Güncellenme tarihi",
    )

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Ders kataloğu"
        ordering = ["course_code"]


class AcademicTerm(models.Model):

    class TermType(models.TextChoices):
        FALL = "FALL", "Güz"
        SPRING = "SPRING", "Bahar"
        SUMMER = "SUMMER", "Yaz"

    academic_year = models.CharField(
        max_length=9,
        validators=[
            RegexValidator(
                regex=r"^\d{4}-\d{4}$",
                message="Akademik yıl 2025-2026 biçiminde olmalıdır.",
            )
        ],
        verbose_name="Akademik yıl",
        help_text="Örnek: 2025-2026",
    )

    term = models.CharField(
        max_length=6,
        choices=TermType.choices,
        verbose_name="Dönem",
    )

    starts_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Başlangıç tarihi",
    )

    ends_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Bitiş tarihi",
    )

    is_current = models.BooleanField(
        default=False,
        verbose_name="Aktif dönem mi?",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturulma tarihi",
    )

    def __str__(self):
        return f"{self.academic_year} {self.get_term_display()}"

    class Meta:
        verbose_name = "Akademik dönem"
        verbose_name_plural = "Akademik dönemler"

        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "term"],
                name="unique_academic_year_term",
            )
        ]

        ordering = ["-academic_year", "term"]


class StudentRequiredCourse(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Aktif"
        REMOVED = "REMOVED", "Listeden çıkarıldı"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="required_courses",
        verbose_name="Öğrenci",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="student_requirements",
        verbose_name="Ders",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Durum",
    )

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="course_requirements_added",
        verbose_name="Ekleyen koordinatör",
    )

    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Eklenme tarihi",
    )

    added_reason = models.TextField(
        blank=True,
        verbose_name="Eklenme gerekçesi",
    )

    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="course_requirements_removed",
        verbose_name="Çıkaran koordinatör",
    )

    removed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Çıkarılma tarihi",
    )

    removed_reason = models.TextField(
        blank=True,
        verbose_name="Çıkarılma gerekçesi",
    )

    def __str__(self):
        return f"{self.student.student_no} - {self.course.course_code}"

    class Meta:
        verbose_name = "Öğrencinin zorunlu dersi"
        verbose_name_plural = "Öğrenci ders listeleri"
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                condition=Q(status="ACTIVE"),
                name="unique_active_student_required_course",
            )
        ]


class CourseAttempt(models.Model):

    class AcademicStatus(models.TextChoices):
        PLANNED = "PLANNED", "Planlandı"
        TAKEN = "TAKEN", "Alındı"
        PASSED = "PASSED", "Geçti"
        FAILED = "FAILED", "Kaldı"
        EXEMPT = "EXEMPT", "Muaf"
        REMOVED = "REMOVED", "Çıkarıldı"

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Onay bekliyor"
        APPROVED = "APPROVED", "Onaylandı"
        REJECTED = "REJECTED", "Reddedildi"
        CANCELLED = "CANCELLED", "İptal edildi"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="course_attempts",
        verbose_name="Öğrenci",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="attempts",
        verbose_name="Ders",
    )

    term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.PROTECT,
        related_name="course_attempts",
        verbose_name="Planlanan veya alınan dönem",
    )

    passed_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="courses_passed_in_term",
        verbose_name="Geçtiği dönem",
    )

    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Not",
    )

    academic_status = models.CharField(
        max_length=10,
        choices=AcademicStatus.choices,
        default=AcademicStatus.PLANNED,
        verbose_name="Ders durumu",
    )

    approval_status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        verbose_name="Onay durumu",
    )

    is_historical = models.BooleanField(
        default=False,
        verbose_name="Geçmiş dönem kaydı mı?",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_course_attempts",
        verbose_name="Kaydı oluşturan",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_course_attempts",
        verbose_name="İnceleyen koordinatör",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="İnceleme tarihi",
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Ret gerekçesi",
    )

    cancellation_reason = models.TextField(
        blank=True,
        verbose_name="İptal gerekçesi",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturulma tarihi",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Son güncellenme tarihi",
    )

    def __str__(self):
        return (
            f"{self.student.student_no} - "
            f"{self.course.course_code} - {self.term}"
        )

    class Meta:
        verbose_name = "Ders denemesi"
        verbose_name_plural = "Ders denemeleri"
        ordering = [
            "student__student_no",
            "term__academic_year",
            "course__course_code",
            "created_at",
        ]        


class GradeSubmission(models.Model):

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Onay bekliyor"
        APPROVED = "APPROVED", "Onaylandı"
        REJECTED = "REJECTED", "Reddedildi"

    class ResultStatus(models.TextChoices):
        PASSED = "PASSED", "Geçti"
        FAILED = "FAILED", "Kaldı"

    course_attempt = models.ForeignKey(
        CourseAttempt,
        on_delete=models.PROTECT,
        related_name="grade_submissions",
        verbose_name="Ders denemesi",
    )

    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Bildirilen not",
    )

    result_status = models.CharField(
        max_length=6,
        choices=ResultStatus.choices,
        null=True,
        blank=True,
        verbose_name="Koordinatörün belirlediği sonuç",
    )

    approval_status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        verbose_name="Not onay durumu",
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="grade_submissions_sent",
        verbose_name="Gönderen öğrenci",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="grade_submissions_reviewed",
        verbose_name="İnceleyen koordinatör",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="İnceleme tarihi",
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Ret gerekçesi",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Gönderim tarihi",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Güncellenme tarihi",
    )

    def __str__(self):
        return (
            f"{self.course_attempt.student.student_no} - "
            f"{self.course_attempt.course.course_code} - "
            f"{self.get_approval_status_display()}"
        )

    class Meta:
        verbose_name = "Not gönderimi"
        verbose_name_plural = "Not gönderimleri"
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["course_attempt"],
                condition=models.Q(approval_status="PENDING"),
                name="one_pending_grade_per_attempt",
            ),
            models.UniqueConstraint(
                fields=["course_attempt"],
                condition=models.Q(approval_status="APPROVED"),
                name="one_approved_grade_per_attempt",
            ),
        ]