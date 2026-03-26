from django.conf import settings
from django.core.mail import send_mail


def send_password_setup_email(user, token: str, setup_url_base: str = None) -> None:
    """
    Send a first-time password setup email to a newly created user.

    Args:
        user: The User instance.
        token: The raw PasswordSetupToken.token string.
        setup_url_base: Base URL of the password-setup page, e.g.
                        "http://localhost:8000/users/setup-password".
                        Falls back to settings.PASSWORD_SETUP_URL_BASE or a
                        sensible default so the email is always sendable.
    """
    if setup_url_base is None:
        setup_url_base = getattr(
            settings,
            "PASSWORD_SETUP_URL_BASE",
            "http://localhost:8000/users/setup-password",
        )

    setup_link = f"{setup_url_base}?token={token}"
    subject = "Set up your Ethiopian Daily account password"
    message = (
        f"Hello {user.get_full_name() or user.email},\n\n"
        "Your account has been created on Ethiopian Daily.\n\n"
        f"Please use the link below to set your password:\n\n"
        f"  {setup_link}\n\n"
        "This link is valid for one use only.\n\n"
        "If you did not expect this email, please ignore it.\n\n"
        "— Ethiopian Daily Team"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ethiopiandaily.com")

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[user.email],
        fail_silently=False,
    )
