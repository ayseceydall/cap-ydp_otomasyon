from django.urls import path

from . import views


urlpatterns = [
    path("", views.document_list, name="document_list"),
    path("yukle/", views.document_upload, name="document_upload"),
    path(
        "<int:pk>/indir/",
        views.document_download,
        name="document_download",
    ),

    path(
    "koordinator/",
    views.coordinator_document_list,
    name="coordinator_document_list",
),
path(
    "koordinator/<int:pk>/karar/",
    views.decide_document,
    name="decide_document",
),



]