from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role")


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):

    add_form = CustomUserCreationForm

    # Mevcut kullanıcıyı düzenlerken gösterilecek alanlar
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Rol Bilgisi", {"fields": ("role",)}),
    )

    # Yeni kullanıcı oluştururken gösterilecek alanlar.
    # usable_password alanını bilerek kullanmıyoruz.
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )