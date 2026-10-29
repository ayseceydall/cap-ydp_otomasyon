from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404

from students.models import StudentProfile

from .forms import (
    CourseAttemptCreateForm,
    GradeSubmissionForm,
)
  
from .models import (
    AcademicTerm,
    Course,
    CourseAttempt,
    GradeSubmission,
    StudentRequiredCourse,
)

from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from documents.models import StudentDocument
from auditlog.services import log_action


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

            log_action(
    actor=request.user,
    action="CREATE",
    instance=attempt,
    summary="Öğrenci ders alma talebi oluşturdu.",
    new_values={
        "course_code": attempt.course.course_code,
        "term": str(attempt.term),
        "approval_status": attempt.approval_status,
    },
    request=request,
)

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

    log_action(
        actor=request.user,
        action=(
            "APPROVE"
            if attempt.approval_status
            == CourseAttempt.ApprovalStatus.APPROVED
            else "REJECT"
        ),
        instance=attempt,
        summary=(
            "Ders alma talebi onaylandı."
            if attempt.approval_status
            == CourseAttempt.ApprovalStatus.APPROVED
            else "Ders alma talebi reddedildi."
        ),
        old_values={
            "approval_status": "PENDING",
        },
        new_values={
            "approval_status": attempt.approval_status,
        },
        reason=attempt.rejection_reason,
        request=request,
    )

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
            attempt = form.cleaned_data["course_attempt"]

            # Öğrencinin ilgili döneme ait ÇAP/YDP
            # transkriptinin mevcut ve erişilebilir
            # bir dosya olması gerekir.
            transcript_documents = StudentDocument.objects.filter(
                student=student,
                document_type=(
                    StudentDocument.DocumentType.CAP_YDP_TRANSCRIPT
                ),
                academic_term=attempt.term,
                status__in=[
                    StudentDocument.Status.PENDING,
                    StudentDocument.Status.APPROVED,
                ],
            )

            transcript_exists = any(
                document.file
                and document.file.storage.exists(document.file.name)
                for document in transcript_documents
            )

            if not transcript_exists:
                form.add_error(
                    "course_attempt",
                    (
                        f"{attempt.term} dönemi için önce "
                        "ÇAP/YDP transkriptini yüklemelisin."
                    ),
                )
            else:
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
    role = str(
        getattr(request.user, "role", "") or ""
    ).strip().lower()

    if role != "coordinator":
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

    result_status = ""

    if action == "approve":
        result_status = request.POST.get(
            "result_status", ""
        ).strip().upper()

        if result_status not in ("PASSED", "FAILED"):
            messages.error(
                request,
                "Notu onaylamadan önce Geçti veya Kaldı seçmelisin.",
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
            submission.result_status = result_status

            attempt = submission.course_attempt
            attempt.grade = submission.grade

            if result_status == "PASSED":
                attempt.academic_status = (
                    CourseAttempt.AcademicStatus.PASSED
                )
            else:
                attempt.academic_status = (
                    CourseAttempt.AcademicStatus.FAILED
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

        log_action(
            actor=request.user,
            action=(
                "APPROVE"
                if action == "approve"
                else "REJECT"
            ),
            instance=submission,
            summary=(
                "Not bildirimi onaylandı."
                if action == "approve"
                else "Not bildirimi reddedildi."
            ),
            old_values={
                "approval_status": "PENDING",
            },
            new_values={
                "approval_status": submission.approval_status,
                "grade": str(submission.grade),
                "result_status": submission.result_status,
            },
            reason=submission.rejection_reason,
            request=request,
        )

    messages.success(
        request,
        "Not değerlendirmesi kaydedildi.",
    )
    return redirect("coordinator_grade_submissions")



@login_required(login_url="/giris/")
def academic_progress(request):
    student = get_current_student(request)

    required_courses = list(
        StudentRequiredCourse.objects.filter(
            student=student,
            status=StudentRequiredCourse.Status.ACTIVE,
        )
        .select_related("course")
        .order_by("course__course_code")
    )

    approved_attempts = list(
        CourseAttempt.objects.filter(
            student=student,
            approval_status=CourseAttempt.ApprovalStatus.APPROVED,
        )
        .exclude(
            academic_status=CourseAttempt.AcademicStatus.REMOVED
        )
        .select_related("course", "term", "passed_term")
        .order_by(
            "term__academic_year",
            "created_at",
            "pk",
        )
    )

    attempts_by_course = {}

    for attempt in approved_attempts:
        attempts_by_course.setdefault(
            attempt.course_id,
            [],
        ).append(attempt)

    progress_rows = []

    for required_course in required_courses:
        course_attempts = attempts_by_course.get(
            required_course.course_id,
            [],
        )

        completed_attempts = [
            attempt
            for attempt in course_attempts
            if attempt.academic_status in (
                CourseAttempt.AcademicStatus.PASSED,
                CourseAttempt.AcademicStatus.EXEMPT,
            )
        ]

        progress_rows.append({
            "required_course": required_course,
            "attempts": course_attempts,
            "attempt_count": len(course_attempts),
            "latest_attempt": (
                course_attempts[-1]
                if course_attempts
                else None
            ),
            "completed": bool(completed_attempts),
            "completion_attempt": (
                completed_attempts[-1]
                if completed_attempts
                else None
            ),
        })

    total_count = len(progress_rows)

    completed_count = sum(
        1 for row in progress_rows if row["completed"]
    )

    remaining_count = total_count - completed_count

    total_credit = sum(
        (
            row["required_course"].course.credit
            for row in progress_rows
        ),
        0,
    )

    completed_credit = sum(
        (
            row["required_course"].course.credit
            for row in progress_rows
            if row["completed"]
        ),
        0,
    )

    total_ects = sum(
        (
            row["required_course"].course.ects
            for row in progress_rows
        ),
        0,
    )

    completed_ects = sum(
        (
            row["required_course"].course.ects
            for row in progress_rows
            if row["completed"]
        ),
        0,
    )

    progress_percent = (
        round(completed_count / total_count * 100)
        if total_count
        else 0
    )

    return render(
        request,
        "academics/academic_progress.html",
        {
            "progress_rows": progress_rows,
            "total_count": total_count,
            "completed_count": completed_count,
            "remaining_count": remaining_count,
            "total_credit": total_credit,
            "completed_credit": completed_credit,
            "remaining_credit": total_credit - completed_credit,
            "total_ects": total_ects,
            "completed_ects": completed_ects,
            "remaining_ects": total_ects - completed_ects,
            "progress_percent": progress_percent,
        },
    )
