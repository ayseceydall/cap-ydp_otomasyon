
from django import forms
from django.contrib.auth import get_user_model
import os

from .models import Message


User = get_user_model()


class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = (
    "recipient",
    "subject",
    "body",
    "attachment",
)

        labels = {
            "recipient": "Alıcı",
            "subject": "Konu",
            "body": "Mesaj içeriği",
            "attachment": "Dosya eki (PDF, JPG veya PNG)",
        }

        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "placeholder": "Mesajın konusu",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Mesajını buraya yaz...",
                }
            ),
            "attachment": forms.FileInput(
                attrs={
                    "accept": ".pdf,.jpg,.jpeg,.png",
                }
            ),
        }


   
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["recipient"].queryset = User.objects.none()

        if user is None:
            return

        allowed_roles = {
            "student": ("coordinator",),
            "coordinator": ("student",),
            "chair": (),
        }

        roles = allowed_roles.get(user.role, ())

        self.fields["recipient"].queryset = (
            User.objects.filter(
                is_active=True,
                role__in=roles,
            )
            .exclude(pk=user.pk)
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )

    def clean_subject(self):
        subject = self.cleaned_data["subject"].strip()

        if not subject:
            raise forms.ValidationError(
                "Mesaj konusu boş olamaz."
            )

        return subject

    def clean_body(self):
        body = self.cleaned_data["body"].strip()

        if not body:
            raise forms.ValidationError(
                "Mesaj içeriği boş olamaz."
            )

        return body

    def clean_attachment(self):
        uploaded_file = self.cleaned_data.get("attachment")

        # Ek dosya isteğe bağlıdır.
        if not uploaded_file:
            return uploaded_file

        # En fazla 5 MB.
        max_size = 5 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise forms.ValidationError(
                "Dosya boyutu en fazla 5 MB olabilir."
            )

        extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        allowed_extensions = {
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
        }

        if extension not in allowed_extensions:
            raise forms.ValidationError(
                "Yalnızca PDF, JPG ve PNG dosyaları yüklenebilir."
            )

        # Uzantıya ek olarak dosyanın başlangıç imzasını kontrol et.
        uploaded_file.seek(0)
        signature = uploaded_file.read(8)
        uploaded_file.seek(0)

        valid_signatures = {
            ".pdf": signature.startswith(b"%PDF-"),
            ".jpg": signature.startswith(b"\xff\xd8\xff"),
            ".jpeg": signature.startswith(b"\xff\xd8\xff"),
            ".png": signature.startswith(
                b"\x89PNG\r\n\x1a\n"
            ),
        }

        if not valid_signatures[extension]:
            raise forms.ValidationError(
                "Dosya içeriği uzantısıyla uyuşmuyor veya dosya geçersiz."
            )

        return uploaded_file

