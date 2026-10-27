from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse


User = get_user_model()


class RoleBasedLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        role = self.request.user.role

        if role == User.Role.COORDINATOR:
            return reverse("student_list")

        if role == User.Role.STUDENT:
            return reverse("my_profile")

        if role == User.Role.CHAIR:
            return reverse("chair_dashboard")

        return reverse("login")
