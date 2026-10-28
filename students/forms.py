
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import StudentProfile


User = get_user_model()


class StudentCreateForm(forms.Form):

    username = forms.CharField(
        label="Kullanıcı adı",
        max_length=150,
    )

    first_name = forms.CharField(
        label="Ad",
        max_length=150,
    )

    last_name = forms.CharField(
        label="Soyad",
        max_length=150,
    )

    email = forms.EmailField(
        label="Okul e-postası",
    )

    student_no = forms.CharField(
        label="Öğrenci numarası",
        max_length=20,
    )

    program_type = forms.ChoiceField(
        label="Program türü",
        choices=StudentProfile.ProgramType.choices,
    )

    acceptance_academic_year = forms.RegexField(
        label="Kabul edildiği akademik yıl",
        regex=r"^\d{4}-\d{4}$",
        error_messages={
            "invalid": "Örnek format: 2025-2026",
        },
    )

    acceptance_term = forms.ChoiceField(
        label="Kabul dönemi",
        choices=StudentProfile.Term.choices,
    )

    temporary_password = forms.CharField(
        label="Geçici parola",
        min_length=10,
        widget=forms.PasswordInput,
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "Bu kullanıcı adı zaten kullanılıyor."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Bu e-posta adresi zaten kayıtlı."
            )

        return email

    def clean_student_no(self):
        student_no = self.cleaned_data["student_no"].strip()

        if StudentProfile.objects.filter(
            student_no=student_no
        ).exists():
            raise forms.ValidationError(
                "Bu öğrenci numarası zaten kayıtlı."
            )

        return student_no

    def clean_temporary_password(self):
        password = self.cleaned_data["temporary_password"]

        candidate_user = User(
            username=self.cleaned_data.get("username", ""),
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
            email=self.cleaned_data.get("email", ""),
        )

        try:
            validate_password(password, user=candidate_user)
        except ValidationError as error:
            raise forms.ValidationError(error.messages)

        return password

    @transaction.atomic
    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["temporary_password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            role=User.Role.STUDENT,
        )

        profile = StudentProfile.objects.create(
            user=user,
            student_no=self.cleaned_data["student_no"],
            program_type=self.cleaned_data["program_type"],
            acceptance_academic_year=(
                self.cleaned_data["acceptance_academic_year"]
            ),
            acceptance_term=self.cleaned_data["acceptance_term"],
        )

        return profile


class GanoUpdateForm(forms.ModelForm):

    class Meta:
        model = StudentProfile
        fields = ("gano", "gano_source")

        labels = {
            "gano": "GANO (Genel Akademik Not Ortalaması)",
            "gano_source": "GANO kaynak bilgisi",
        }

        widgets = {
            "gano": forms.NumberInput(
                attrs={
                    "min": "0",
                    "max": "4",
                    "step": "0.01",
                    "placeholder": "Örn. 3.25",
                }
            ),
            "gano_source": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Örn. Öğrencinin resmî transkripti"
                    ),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        gano = cleaned_data.get("gano")
        source = (
            cleaned_data.get("gano_source") or ""
        ).strip()

        if gano is not None and not source:
            self.add_error(
                "gano_source",
                "GANO girildiğinde kaynak bilgisi zorunludur.",
            )

        cleaned_data["gano_source"] = source

        return cleaned_data

    

