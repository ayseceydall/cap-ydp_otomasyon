
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError(
            "İşlem geçmişi kayıtları değiştirilemez."
        )

    def delete(self):
        raise ValidationError(
            "İşlem geçmişi kayıtları silinemez."
        )


class AuditLogManager(
    models.Manager.from_queryset(AuditLogQuerySet)
):
    pass


class AuditLog(models.Model):

    class Action(models.TextChoices):
        CREATE = "CREATE", "Oluşturma"
        UPDATE = "UPDATE", "Güncelleme"
        APPROVE = "APPROVE", "Onaylama"
        REJECT = "REJECT", "Reddetme"
        CANCEL = "CANCEL", "İptal"
        UPLOAD = "UPLOAD", "Belge yükleme"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="İşlemi yapan kullanıcı",
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name="İşlem türü",
    )

    model_label = models.CharField(
        max_length=100,
        verbose_name="İlgili model",
    )

    object_id = models.CharField(
        max_length=100,
        verbose_name="İlgili kayıt numarası",
    )

    summary = models.CharField(
        max_length=255,
        verbose_name="İşlem açıklaması",
    )

    old_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Önceki değerler",
    )

    new_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Yeni değerler",
    )

    reason = models.TextField(
        blank=True,
        verbose_name="İşlem gerekçesi",
    )

    request_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="İşlem yapılan adres",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="İşlem tarihi",
    )

    objects = AuditLogManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "İşlem geçmişi kaydı"
        verbose_name_plural = "İşlem geçmişi kayıtları"

    def save(self, *args, **kwargs):
        if (
            self.pk is not None
            and type(self).objects.filter(pk=self.pk).exists()
        ):
            raise ValidationError(
                "İşlem geçmişi kayıtları değiştirilemez."
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "İşlem geçmişi kayıtları silinemez."
        )

    def __str__(self):
        return (
            f"{self.get_action_display()} - "
            f"{self.model_label} #{self.object_id}"
        )
