from pathlib import Path

from django import forms

from academics.models import AcademicTerm
from .models import StudentDocument


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_SIGNATURES = {
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}


class StudentDocumentUploadForm(forms.ModelForm):

    class Meta:
        model = StudentDocument
        fields = [
            "document_type",
            "academic_term",
            "title",
            "file",
        ]

        labels = {
            "document_type": "Belge türü",
            "academic_term": "Akademik dönem",
            "title": "Belge başlığı",
            "file": "Dosya seç",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["academic_term"].queryset = (
            AcademicTerm.objects.order_by(
                "-academic_year",
                "term",
            )
        )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]

        if uploaded_file.size > MAX_FILE_SIZE:
            raise forms.ValidationError(
                "Dosya boyutu en fazla 5 MB olabilir."
            )

        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_SIGNATURES:
            raise forms.ValidationError(
                "Yalnızca PDF, PNG, JPG ve JPEG dosyaları kabul edilir."
            )

        if ":" in uploaded_file.name:
            raise forms.ValidationError(
                "Dosya adı geçersiz karakter içeriyor."
            )

        header = uploaded_file.read(16)
        uploaded_file.seek(0)

        expected_signatures = ALLOWED_SIGNATURES[extension]

        if not any(
            header.startswith(signature)
            for signature in expected_signatures
        ):
            raise forms.ValidationError(
                "Dosyanın içeriği uzantısıyla eşleşmiyor."
            )

        return uploaded_file