import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from students.models import StudentProfile
from academics.models import AcademicTerm


def document_upload_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower()

    # Öğrenci numarası veya yüklenen dosyanın adı
    # depolama yolunda kullanılmaz.
    return f"student_documents/{uuid.uuid4().hex}{extension}"


class StudentDocument(models.Model):

    class DocumentType(models.TextChoices):
        CAP_YDP_TRANSCRIPT = (
            "CAP_YDP_TRANSCRIPT",
            "ÇAP/YDP transkripti",
        )
        MAIN_TRANSCRIPT = (
            "MAIN_TRANSCRIPT",
            "Ana dal transkripti",
        )
        SIGNED_FORM = "SIGNED_FORM", "İmzalı form"
        OFFICIAL_LETTER = "OFFICIAL_LETTER", "Resmî yazı"
        OTHER = "OTHER", "Diğer"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Onay bekliyor"
        APPROVED = "APPROVED", "Onaylandı"
        REJECTED = "REJECTED", "Reddedildi"
        CANCELLED = "CANCELLED", "İptal edildi"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="Öğrenci",
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        verbose_name="Belge türü",
    )

    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="student_documents",
        verbose_name="Akademik dönem",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Belge başlığı",
    )

    file = models.FileField(
        upload_to=document_upload_path,
        verbose_name="Dosya",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Belge durumu",
    )

    version = models.PositiveIntegerField(
        default=1,
        verbose_name="Belge sürümü",
    )

    previous_version = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="new_versions",
        verbose_name="Önceki sürüm",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_student_documents",
        verbose_name="Yükleyen kullanıcı",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_student_documents",
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
        verbose_name="Yüklenme tarihi",
    )

    def clean(self):
        super().clean()

        if (
            self.document_type == self.DocumentType.CAP_YDP_TRANSCRIPT
            and not self.academic_term_id
        ):
            raise ValidationError({
                "academic_term": (
                    "ÇAP/YDP transkripti için akademik dönem seçilmelidir."
                )
            })

        if self.previous_version_id:
            previous = self.previous_version

            if previous.student_id != self.student_id:
                raise ValidationError({
                    "previous_version": (
                        "Önceki sürüm aynı öğrenciye ait olmalıdır."
                    )
                })

            if previous.document_type != self.document_type:
                raise ValidationError({
                    "previous_version": (
                        "Belge sürümlerinin türü aynı olmalıdır."
                    )
                })

            if previous.academic_term_id != self.academic_term_id:
                raise ValidationError({
                    "previous_version": (
                        "Belge sürümlerinin dönemi aynı olmalıdır."
                    )
                })

            if self.version != previous.version + 1:
                raise ValidationError({
                    "version": (
                        "Yeni sürüm, önceki sürümün bir fazlası olmalıdır."
                    )
                })

    def __str__(self):
        return (
            f"{self.student.student_no} - "
            f"{self.get_document_type_display()} - "
            f"v{self.version}"
        )

    class Meta:
        verbose_name = "Öğrenci belgesi"
        verbose_name_plural = "Öğrenci belgeleri"
        ordering = ["-created_at"]