from django.urls import path

from . import views


urlpatterns = [
    path("", views.student_list, name="student_list"),
    path("yeni/", views.student_create, name="student_create"),
     path("panelim/", views.my_profile, name="my_profile"),
    path("izleme/", views.chair_dashboard, name="chair_dashboard"),
    path(
    "<int:pk>/gano/",
    views.coordinator_update_gano,
    name="coordinator_update_gano",
),
]