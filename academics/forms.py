from django import forms

from .models import Course, AcademicTerm, CourseAttempt


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