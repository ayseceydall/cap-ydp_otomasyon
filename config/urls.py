from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("ogrenciler/", include("students.urls")),
    path("akademik/", include("academics.urls")),
]