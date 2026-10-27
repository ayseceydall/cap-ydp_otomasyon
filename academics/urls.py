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

]