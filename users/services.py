"""
Service layer for user management.

All business logic (creation, password setup, role enforcement) lives here so
it works independently of any HTTP layer.
"""
import secrets

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError

from .emails import send_password_setup_email
from .models import PasswordSetupToken, User


class UserService:
    """Handles admin-level user lifecycle operations."""

    # --- Creation ---

    @staticmethod
    def create_user(
        *,
        acting_user: User,
        email: str,
        role: str,
        first_name: str = "",
        last_name: str = "",
        send_email: bool = True,
    ) -> User:
        """
        Create a new user.  Only admins may call this.

        The new user is created with an unusable password and a one-time token
        is generated.  An email with a setup link is sent unless send_email=False
        (useful in tests).

        Returns the newly created User.
        """
        if not acting_user.is_admin():
            raise PermissionDenied("Only admins can create users.")

        if role not in User.Role.values:
            raise ValidationError(f"Invalid role '{role}'. Choose from {User.Role.values}.")

        user = User.objects.create_user(
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )

        token_str = UserService._generate_setup_token(user)

        if send_email:
            send_password_setup_email(user, token_str)

        return user

    # --- Password setup ---

    @staticmethod
    def setup_password(*, token_str: str, new_password: str) -> User:
        """
        Called when a new user clicks their setup link and submits a password.

        Validates the token, validates the password, sets it, and marks
        must_change_password=False.

        Returns the updated User.
        Raises ValidationError or PasswordSetupToken.DoesNotExist on failure.
        """
        try:
            token_obj = PasswordSetupToken.objects.select_related("user").get(
                token=token_str,
                is_used=False,
            )
        except PasswordSetupToken.DoesNotExist:
            raise ValidationError("Invalid or already-used password setup token.")

        if token_obj.is_expired():
            raise ValidationError("This setup link has expired. Ask an admin to resend it.")

        user = token_obj.user

        # Run Django's built-in password validators.
        validate_password(new_password, user=user)

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

        token_obj.is_used = True
        token_obj.save(update_fields=["is_used"])

        return user

    # --- Re-send setup email ---

    @staticmethod
    def resend_setup_email(*, acting_user: User, target_user: User) -> None:
        """
        Admin can trigger a new setup email for a user who hasn't set their password.
        Invalidates any existing token and issues a fresh one.
        """
        if not acting_user.is_admin():
            raise PermissionDenied("Only admins can resend setup emails.")

        target_user.refresh_from_db()
        if not target_user.must_change_password:
            raise ValidationError("This user has already set their password.")

        # Rotate the token.
        PasswordSetupToken.objects.filter(user=target_user).delete()
        token_str = UserService._generate_setup_token(target_user)
        send_password_setup_email(target_user, token_str)

    # --- Role enforcement helpers ---

    @staticmethod
    def assert_can_manage_users(user: User) -> None:
        """Raises PermissionDenied if the user is not an admin."""
        if not user.is_admin():
            raise PermissionDenied("Only admins can manage users.")

    @staticmethod
    def assert_can_write_articles(user: User) -> None:
        """Raises PermissionDenied if the user is not a writer or admin."""
        if not (user.is_writer() or user.is_admin()):
            raise PermissionDenied("Only writers and admins can create articles.")

    @staticmethod
    def assert_can_review_articles(user: User) -> None:
        """Raises PermissionDenied if the user is not a reviewer or admin."""
        if not (user.is_reviewer() or user.is_admin()):
            raise PermissionDenied("Only reviewers and admins can review articles.")

    # --- Internal helpers ---

    @staticmethod
    def _generate_setup_token(user: User) -> str:
        """Creates a PasswordSetupToken for user and returns the raw token string."""
        token_str = secrets.token_urlsafe(48)
        PasswordSetupToken.objects.create(user=user, token=token_str)
        return token_str
