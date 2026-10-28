from django.urls import path

from . import views


urlpatterns = [
    path(
        "derslerim/",
        views.course_attempt_list,
        name="course_attempt_list",
    ),
    path(
        "derslerim/yeni/",
        views.course_attempt_create,
        name="course_attempt_create",
    ),


    path(
    "koordinator/onaylar/",
    views.coordinator_course_attempts,
    name="coordinator_course_attempts",
),
path(
    "koordinator/onaylar/<int:pk>/",
    views.decide_course_attempt,
    name="course_attempt_decide",
),

path(
    "notlarim/",
    views.grade_submission_list,
    name="grade_submission_list",
),
path(
    "notlarim/yeni/",
    views.grade_submission_create,
    name="grade_submission_create",
),


path(
    "koordinator/not-onaylari/",
    views.coordinator_grade_submissions,
    name="coordinator_grade_submissions",
),
path(
    "koordinator/not-onaylari/<int:pk>/",
    views.decide_grade_submission,
    name="decide_grade_submission",
),


path(
    "ilerlemem/",
    views.academic_progress,
    name="academic_progress",
),

]