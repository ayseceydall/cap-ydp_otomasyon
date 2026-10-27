from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path(
        "",
        RedirectView.as_view(url="/giris/", permanent=False),
        name="home",
    ),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("ogrenciler/", include("students.urls")),
    path("akademik/", include("academics.urls")),
    path("belgeler/", include("documents.urls")),
]
