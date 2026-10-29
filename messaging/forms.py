
from django import forms
from django.contrib.auth import get_user_model

from .models import Message


User = get_user_model()


class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = (
            "recipient",
            "subject",
            "body",
        )

        labels = {
            "recipient": "Alıcı",
            "subject": "Konu",
            "body": "Mesaj içeriği",
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
