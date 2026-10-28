from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET

from students.models import StudentProfile
from .forms import StudentDocumentUploadForm  # type: ignore[reportMissingImports]
from .models import StudentDocument
from auditlog.services import log_action
from django.utils import timezone
from django.views.decorators.http import require_POST


@login_required(login_url="/giris/")
def document_list(request):

    if request.user.role == "student":
        student = get_object_or_404(
            StudentProfile,
            user=request.user,
        )

        documents = StudentDocument.objects.filter(
            student=student
        )

    elif request.user.role in ("coordinator", "chair"):
        documents = StudentDocument.objects.all()

    else:
        raise PermissionDenied

    documents = documents.select_related(
        "student",
        "academic_term",
        "uploaded_by",
        "reviewed_by",
    ).order_by("-created_at")

    return render(
        request,
        "documents/document_list.html",
        {"documents": documents},
    )



@login_required(login_url="/giris/")
def document_upload(request):

    if request.user.role != "student":
        raise PermissionDenied

    student = get_object_or_404(
        StudentProfile,
        user=request.user,
    )

    if request.method == "POST":
        form = StudentDocumentUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            document = form.save(commit=False)

            document.student = student
            document.uploaded_by = request.user
            document.status = StudentDocument.Status.PENDING
            document.version = 1

            document.save()

            log_action(
                actor=request.user,
                action="UPLOAD",
                instance=document,
                summary="Öğrenci belge yükledi.",
                new_values={
                    "document_type": document.document_type,
                    "academic_term": (
                        str(document.academic_term)
                        if document.academic_term
                        else ""
                    ),
                    "version": document.version,
                    "status": document.status,
                },
                request=request,
            )

            messages.success(
                request,
                "Belgen yüklendi ve koordinatörün incelemesine gönderildi.",
            )

            return redirect("document_list")

    else:
        form = StudentDocumentUploadForm()

    return render(
        request,
        "documents/document_upload.html",
        {"form": form},
    )



@login_required(login_url="/giris/")
@require_GET
def document_download(request, pk):

    document = get_object_or_404(
        StudentDocument,
        pk=pk,
    )

    if request.user.role == "student":
        if document.student.user_id != request.user.id:
            raise PermissionDenied

    elif request.user.role not in ("coordinator", "chair"):
        raise PermissionDenied

    if not document.file:
        raise Http404("Belge dosyası bulunamadı.")

    try:
        file_handle = document.file.open("rb")
    except (OSError, ValueError):
        raise Http404("Belge dosyası bulunamadı.")

    filename = Path(document.file.name).name

    return FileResponse(
        file_handle,
        as_attachment=True,
        filename=filename,
    )



@login_required(login_url="/giris/")
def coordinator_document_list(request):
    if request.user.role != "coordinator":
        raise PermissionDenied

    documents = (
        StudentDocument.objects
        .select_related("student", "uploaded_by", "academic_term")
        .filter(status=StudentDocument.Status.PENDING)
        .order_by("created_at")
    )

    return render(
        request,
        "documents/coordinator_document_list.html",
        {"documents": documents},
    )


@login_required(login_url="/giris/")
@require_POST
def decide_document(request, pk):
    if request.user.role != "coordinator":
        raise PermissionDenied

    document = get_object_or_404(
        StudentDocument,
        pk=pk,
    )

    if document.status != StudentDocument.Status.PENDING:
        messages.error(
            request,
            "Bu belge daha önce değerlendirilmiş.",
        )
        return redirect("coordinator_document_list")

    action = request.POST.get("action")
    reason = request.POST.get("rejection_reason", "").strip()

    if action == "approve":
        document.status = StudentDocument.Status.APPROVED
        document.rejection_reason = ""

    elif action == "reject":
        if not reason:
            messages.error(
                request,
                "Belgeyi reddetmek için gerekçe yazmalısın.",
            )
            return redirect("coordinator_document_list")

        document.status = StudentDocument.Status.REJECTED
        document.rejection_reason = reason

    else:
        messages.error(request, "Geçersiz işlem.")
        return redirect("coordinator_document_list")

    document.reviewed_by = request.user
    document.reviewed_at = timezone.now()

    document.save(
        update_fields=[
            "status",
            "rejection_reason",
            "reviewed_by",
            "reviewed_at",
        ]
    )

    log_action(
        actor=request.user,
        action=(
            "APPROVE"
            if action == "approve"
            else "REJECT"
        ),
        instance=document,
        summary=(
            "Belge onaylandı."
            if action == "approve"
            else "Belge reddedildi."
        ),
        old_values={
            "status": "PENDING",
        },
        new_values={
            "status": document.status,
            "document_type": document.document_type,
        },
        reason=document.rejection_reason,
        request=request,
    )

    messages.success(
        request,
        "Belge değerlendirmesi kaydedildi.",
    )

    return redirect("coordinator_document_list")
