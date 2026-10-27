from django.urls import path
from .views import RoleBasedLoginView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path(
        "giris/",
        RoleBasedLoginView.as_view(),
        name="login",
    ),
    path(
        "cikis/",
        LogoutView.as_view(next_page="login"),
        name="logout",
    ),
]