from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import PasswordSetupToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "role", "is_active", "must_change_password", "date_joined")
    list_filter = ("role", "is_active", "must_change_password")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Role & Status"), {"fields": ("role", "must_change_password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )


@admin.register(PasswordSetupToken)
class PasswordSetupTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "is_used")
    list_filter = ("is_used",)
    readonly_fields = ("token", "created_at")
    search_fields = ("user__email",)
