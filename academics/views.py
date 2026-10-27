from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from students.models import StudentProfile

from .forms import CourseAttemptCreateForm
from .models import CourseAttempt

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