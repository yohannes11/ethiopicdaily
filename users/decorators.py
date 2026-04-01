"""
Permission decorators for users app views.
Kept separate from core/decorators.py to avoid circular imports.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    """Redirect non-admins away from user-management views."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/users/login/?next={request.path}")
        if not request.user.is_admin():
            messages.error(request, "Only admins can access user management.")
            return redirect("users:login")
        return view_func(request, *args, **kwargs)
    return wrapper
