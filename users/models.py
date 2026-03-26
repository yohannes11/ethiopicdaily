from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import CustomUserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        WRITER = "writer", _("Writer")
        REVIEWER = "reviewer", _("Reviewer")
        ADMIN = "admin", _("Admin")

    # Override username to be non-required; email is the primary identifier.
    username = models.CharField(max_length=150, unique=True, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WRITER)
    must_change_password = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "role"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def save(self, *args, **kwargs):
        # Auto-derive username from email if not set.
        if not self.username:
            base = self.email.split("@")[0]
            username = base
            counter = 1
            while User.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{base}{counter}"
                counter += 1
            self.username = username
        super().save(*args, **kwargs)

    # --- Role helpers ---

    def is_writer(self) -> bool:
        return self.role == self.Role.WRITER

    def is_reviewer(self) -> bool:
        return self.role == self.Role.REVIEWER

    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    def __str__(self):
        return f"{self.email} ({self.role})"


class PasswordSetupToken(models.Model):
    """One-time token sent to a new user to let them set their password."""

    TOKEN_EXPIRY_HOURS = 24

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="password_setup_token",
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("password setup token")
        verbose_name_plural = _("password setup tokens")

    def is_expired(self) -> bool:
        expiry = self.created_at + timezone.timedelta(hours=self.TOKEN_EXPIRY_HOURS)
        return timezone.now() > expiry

    def __str__(self):
        return f"Token for {self.user.email} (used={self.is_used})"
