from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Manager for User model where email is the unique identifier instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        # New users cannot log in until they set a password via the setup link.
        extra_fields.setdefault("must_change_password", True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("must_change_password", False)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)
