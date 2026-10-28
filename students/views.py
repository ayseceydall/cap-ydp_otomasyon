from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .forms import StudentCreateForm
from .models import StudentProfile
from auditlog.services import log_action


def require_coordinator(request):
    if request.user.role != "coordinator":
        raise PermissionDenied


@login_required(login_url="/giris/")
def student_list(request):
    require_coordinator(request)

    query = request.GET.get("q", "").strip()

    students = StudentProfile.objects.select_related(
        "user"
    ).all()

    if query:
        students = students.filter(
            Q(student_no__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
        )

    return render(
        request,
        "students/student_list.html",
        {
            "students": students,
            "query": query,
        },
    )


@login_required(login_url="/giris/")
def student_create(request):
    require_coordinator(request)

    if request.method == "POST":
        form = StudentCreateForm(request.POST)

        if form.is_valid():
            profile = form.save()

            log_action(
    actor=request.user,
    action="CREATE",
    instance=profile,
    summary="Yeni öğrenci kaydı oluşturuldu.",
    new_values={
        "student_no": profile.student_no,
        "program_type": profile.program_type,
        "status": profile.status,
    },
    request=request,
)

            messages.success(
                request,
                f"{profile.student_no} numaralı öğrenci oluşturuldu.",
            )

            return redirect("student_list")

    else:
        form = StudentCreateForm()

    return render(
        request,
        "students/student_form.html",
        {"form": form},
    )


@login_required(login_url="/giris/")
def my_profile(request):
    if request.user.role != "student":
        raise PermissionDenied

    student = get_object_or_404(
        StudentProfile.objects.select_related("user"),
        user=request.user,
    )

    return render(
        request,
        "students/my_profile.html",
        {"student": student},
    )


@login_required(login_url="/giris/")
def chair_dashboard(request):
    if request.user.role != "chair":
        raise PermissionDenied

    students = StudentProfile.objects.select_related(
        "user"
    ).all()

    return render(
        request,
        "students/chair_dashboard.html",
        {"students": students},
    )