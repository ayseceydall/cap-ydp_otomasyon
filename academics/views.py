from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from students.models import StudentProfile

from .forms import (
    CourseAttemptCreateForm,
    GradeSubmissionForm,
)
from .models import CourseAttempt, GradeSubmission

from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST


def get_current_student(request):
    if request.user.role != "student":
        raise PermissionDenied

    return get_object_or_404(
        StudentProfile,
        user=request.user,
    )


@login_required(login_url="/giris/")
def course_attempt_list(request):
    student = get_current_student(request)

    attempts = CourseAttempt.objects.filter(
        student=student
    ).select_related(
        "course",
        "term",
        "passed_term",
    ).order_by("-created_at")

    return render(
        request,
        "academics/course_attempt_list.html",
        {"attempts": attempts},
    )


@login_required(login_url="/giris/")
def course_attempt_create(request):
    student = get_current_student(request)

    if request.method == "POST":
        form = CourseAttemptCreateForm(
            request.POST,
            student=student,
        )

        if form.is_valid():
            attempt = form.save(commit=False)

            attempt.student = student
            attempt.created_by = request.user

            # Öğrencinin gönderdiği kayıt henüz onaylı değil.
            attempt.academic_status = (
                CourseAttempt.AcademicStatus.PLANNED
            )
            attempt.approval_status = (
                CourseAttempt.ApprovalStatus.PENDING
            )

            attempt.save()

            messages.success(
                request,
                "Ders kaydın koordinatörün onayına gönderildi.",
            )

            return redirect("course_attempt_list")

    else:
        form = CourseAttemptCreateForm(student=student)

    return render(
        request,
        "academics/course_attempt_form.html",
        {"form": form},
    )

@login_required(login_url="/giris/")
def coordinator_course_attempts(request):
    if request.user.role != "coordinator":
        raise PermissionDenied

    attempts = CourseAttempt.objects.filter(
        approval_status=CourseAttempt.ApprovalStatus.PENDING
    ).select_related(
        "student",
        "student__user",
        "course",
        "term",
    ).order_by("created_at")

    return render(
        request,
        "academics/coordinator_course_attempts.html",
        {"attempts": attempts},
    )


@login_required(login_url="/giris/")
@require_POST
def decide_course_attempt(request, pk):
    if request.user.role != "coordinator":
        raise PermissionDenied

    attempt = get_object_or_404(
        CourseAttempt,
        pk=pk,
    )

    if attempt.approval_status != CourseAttempt.ApprovalStatus.PENDING:
        messages.error(
            request,
            "Bu kayıt daha önce değerlendirilmiş.",
        )
        return redirect("coordinator_course_attempts")

    action = request.POST.get("action")

    if action == "approve":
        attempt.approval_status = (
            CourseAttempt.ApprovalStatus.APPROVED
        )
        attempt.rejection_reason = ""

    elif action == "reject":
        reason = request.POST.get("rejection_reason", "").strip()

        if not reason:
            messages.error(
                request,
                "Reddetmek için bir gerekçe yazmalısın.",
            )
            return redirect("coordinator_course_attempts")

        attempt.approval_status = (
            CourseAttempt.ApprovalStatus.REJECTED
        )
        attempt.rejection_reason = reason

    else:
        messages.error(request, "Geçersiz işlem.")
        return redirect("coordinator_course_attempts")

    attempt.reviewed_by = request.user
    attempt.reviewed_at = timezone.now()

    attempt.save()

    messages.success(request, "İşlem başarıyla kaydedildi.")

    return redirect("coordinator_course_attempts")


@login_required(login_url="/giris/")
def grade_submission_list(request):
    student = get_current_student(request)

    submissions = GradeSubmission.objects.filter(
        course_attempt__student=student
    ).select_related(
        "course_attempt__course",
        "course_attempt__term",
    ).order_by("-created_at")

    return render(
        request,
        "academics/grade_submission_list.html",
        {"submissions": submissions},
    )


@login_required(login_url="/giris/")
def grade_submission_create(request):
    student = get_current_student(request)

    eligible_attempts = CourseAttempt.objects.filter(
        student=student,
        approval_status=CourseAttempt.ApprovalStatus.APPROVED,
    ).exclude(
        grade_submissions__approval_status__in=[
            GradeSubmission.ApprovalStatus.PENDING,
            GradeSubmission.ApprovalStatus.APPROVED,
        ]
    ).select_related(
        "course",
        "term",
    ).distinct()

    if request.method == "POST":
        form = GradeSubmissionForm(
            request.POST,
            student=student,
            eligible_attempts=eligible_attempts,
        )

        if form.is_valid():
            submission = form.save(commit=False)

            submission.submitted_by = request.user
            submission.approval_status = (
                GradeSubmission.ApprovalStatus.PENDING
            )

            submission.save()

            messages.success(
                request,
                "Notun koordinatörün onayına gönderildi.",
            )

            return redirect("grade_submission_list")

    else:
        form = GradeSubmissionForm(
            student=student,
            eligible_attempts=eligible_attempts,
        )

    return render(
        request,
        "academics/grade_submission_form.html",
        {
            "form": form,
            "has_eligible_courses": eligible_attempts.exists(),
        },
    )


@login_required(login_url="/giris/")
def coordinator_grade_submissions(request):
    if request.user.role != "coordinator":
        raise PermissionDenied

    submissions = GradeSubmission.objects.filter(
        approval_status=GradeSubmission.ApprovalStatus.PENDING
    ).select_related(
        "course_attempt__student__user",
        "course_attempt__course",
        "course_attempt__term",
        "submitted_by",
    ).order_by("created_at")

    return render(
        request,
        "academics/coordinator_grade_submissions.html",
        {"submissions": submissions},
    )



@login_required(login_url="/giris/")
@require_POST
def decide_grade_submission(request, pk):
    if request.user.role != "coordinator":
        raise PermissionDenied

    action = request.POST.get("action")

    if action not in ("approve", "reject"):
        messages.error(request, "Geçersiz işlem.")
        return redirect("coordinator_grade_submissions")

    reason = request.POST.get("rejection_reason", "").strip()

    if action == "reject" and not reason:
        messages.error(
            request,
            "Notu reddetmek için gerekçe yazmalısın.",
        )
        return redirect("coordinator_grade_submissions")

    with transaction.atomic():
        submission = get_object_or_404(
            GradeSubmission.objects.select_for_update(),
            pk=pk,
        )

        if submission.approval_status != (
            GradeSubmission.ApprovalStatus.PENDING
        ):
            messages.error(
                request,
                "Bu not daha önce değerlendirilmiş.",
            )
            return redirect("coordinator_grade_submissions")

        if action == "approve":
            submission.approval_status = (
                GradeSubmission.ApprovalStatus.APPROVED
            )
            submission.rejection_reason = ""

            # Onaylanan notu ders denemesine aktar.
            attempt = submission.course_attempt
            attempt.grade = submission.grade
            attempt.academic_status = (
                CourseAttempt.AcademicStatus.TAKEN
            )
            attempt.save(
                update_fields=[
                    "grade",
                    "academic_status",
                    "updated_at",
                ]
            )

        else:
            submission.approval_status = (
                GradeSubmission.ApprovalStatus.REJECTED
            )
            submission.rejection_reason = reason

        submission.reviewed_by = request.user
        submission.reviewed_at = timezone.now()
        submission.save()

    messages.success(request, "Not değerlendirmesi kaydedildi.")

    return redirect("coordinator_grade_submissions")