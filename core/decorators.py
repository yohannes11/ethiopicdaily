"""
Permission decorators for core views.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def _redirect_to_login(request):
    return redirect(f"{reverse('users:login')}?next={request.path}")


def writer_required(view_func):
    """Allow writers and admins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not (request.user.is_writer() or request.user.is_admin()):
            messages.error(request, "You need a writer or admin account to access the newsroom.")
            return redirect("core:homepage")
        return view_func(request, *args, **kwargs)
    return wrapper


def reviewer_required(view_func):
    """Allow reviewers and admins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not (request.user.is_reviewer() or request.user.is_admin()):
            messages.error(request, "You need a reviewer or admin account to access the review queue.")
            return redirect("core:homepage")
        return view_func(request, *args, **kwargs)
    return wrapper


def cms_required(view_func):
    """Any authenticated CMS user (writer, reviewer, or admin)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not (request.user.is_writer() or request.user.is_reviewer() or request.user.is_admin()):
            messages.error(request, "You need a CMS account to access this page.")
            return redirect("core:homepage")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Admins only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _redirect_to_login(request)
        if not request.user.is_admin():
            messages.error(request, "Only admins can access this page.")
            return redirect("core:homepage")
        return view_func(request, *args, **kwargs)
    return wrapper
