from django import forms

from .models import (
    Course,
    AcademicTerm,
    CourseAttempt,
    GradeSubmission,
)


class CourseAttemptCreateForm(forms.ModelForm):

    class Meta:
        model = CourseAttempt
        fields = ["course", "term"]
        labels = {
            "course": "Ders",
            "term": "Akademik dönem",
        }

    def __init__(self, *args, student=None, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)

        self.fields["course"].queryset = Course.objects.filter(
            is_active=True
        ).order_by("course_code")

        self.fields["term"].queryset = AcademicTerm.objects.order_by(
            "-academic_year",
            "term",
        )

    def clean(self):
        cleaned_data = super().clean()

        course = cleaned_data.get("course")
        term = cleaned_data.get("term")

        if self.student and course and term:
            existing = CourseAttempt.objects.filter(
                student=self.student,
                course=course,
                term=term,
            ).exclude(
                approval_status__in=[
                    CourseAttempt.ApprovalStatus.REJECTED,
                    CourseAttempt.ApprovalStatus.CANCELLED,
                ]
            )

            if existing.exists():
                self.add_error(
                    "course",
                    "Bu ders bu dönem için zaten kayıtlı "
                    "veya onay bekliyor.",
                )

        return cleaned_data

class GradeSubmissionForm(forms.ModelForm):

    course_attempt = forms.ModelChoiceField(
        queryset=CourseAttempt.objects.none(),
        label="Ders",
        empty_label="Ders seçiniz",
    )

    grade = forms.DecimalField(
        label="Dönem sonu notu",
        min_value=0,
        max_value=100,
        max_digits=5,
        decimal_places=2,
        help_text="Notu 0 ile 100 arasında giriniz.",
    )

    class Meta:
        model = GradeSubmission
        fields = ["course_attempt", "grade"]

    def __init__(
        self,
        *args,
        student=None,
        eligible_attempts=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if student is not None and eligible_attempts is not None:
            self.fields["course_attempt"].queryset = (
                eligible_attempts.filter(
                    student=student,
                    approval_status=(
                        CourseAttempt.ApprovalStatus.APPROVED
                    ),
                )
            )