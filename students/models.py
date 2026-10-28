from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class StudentProfile(models.Model):

    class ProgramType(models.TextChoices):
        CAP = "CAP", "Çift Anadal (ÇAP)"
        YDP = "YDP", "Yan Dal (YDP)"

    class Term(models.TextChoices):
        FALL = "FALL", "Güz"
        SPRING = "SPRING", "Bahar"
        SUMMER = "SUMMER", "Yaz"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Aktif"
        GRADUATED = "GRADUATED", "Mezun"
        CERTIFICATE_COMPLETED = (
            "CERTIFICATE_COMPLETED",
            "Sertifika tamamlandı",
        )
        CANCELLED = "CANCELLED", "İptal edildi"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="student_profile",
        verbose_name="Kullanıcı hesabı",
    )

    student_no = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Öğrenci numarası",
    )

    program_type = models.CharField(
        max_length=3,
        choices=ProgramType.choices,
        verbose_name="Program türü",
    )

    acceptance_academic_year = models.CharField(
        max_length=9,
        verbose_name="Kabul edildiği akademik yıl",
        help_text="Örnek: 2025-2026",
    )

    acceptance_term = models.CharField(
        max_length=6,
        choices=Term.choices,
        verbose_name="Kabul dönemi",
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Öğrenci durumu",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturulma tarihi",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Son güncellenme tarihi",
    )



    gano = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(4),
        ],
        verbose_name="GANO",
        help_text="0.00 ile 4.00 arasında olmalıdır.",
    )

    gano_source = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="GANO kaynağı",
        help_text="Örn. resmî transkript veya öğrenci belgesi.",
    )

    gano_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gano_updates",
        verbose_name="GANO güncelleyen",
    )

    gano_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="GANO güncellenme tarihi",
    )



def __str__(self):
        return f"{self.student_no} - {self.user.get_full_name() or self.user.username}"

class Meta:
        verbose_name = "Öğrenci"
        verbose_name_plural = "Öğrenciler"
        ordering = ["student_no"]