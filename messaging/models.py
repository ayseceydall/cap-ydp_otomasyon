
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class MessageQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError(
            "Mesajlar silinemez; mesaj geçmişi korunmalıdır."
        )


class MessageManager(
    models.Manager.from_queryset(MessageQuerySet)
):
    pass


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_messages",
        verbose_name="Gönderen",
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_messages",
        verbose_name="Alıcı",
    )

    subject = models.CharField(
        max_length=200,
        verbose_name="Konu",
    )

    body = models.TextField(
        verbose_name="Mesaj içeriği",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Gönderim tarihi",
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Okunma tarihi",
    )

    objects = MessageManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mesaj"
        verbose_name_plural = "Mesajlar"

    def clean(self):
        super().clean()

        if (
            self.sender_id is not None
            and self.sender_id == self.recipient_id
        ):
            raise ValidationError(
                "Kendine mesaj gönderemezsin."
            )

        if not self.subject.strip():
            raise ValidationError(
                {"subject": "Mesaj konusu boş olamaz."}
            )

        if not self.body.strip():
            raise ValidationError(
                {"body": "Mesaj içeriği boş olamaz."}
            )

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Mesajlar silinemez; mesaj geçmişi korunmalıdır."
        )

    def __str__(self):
        return f"{self.subject} - {self.sender}"
