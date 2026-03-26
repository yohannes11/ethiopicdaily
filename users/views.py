from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .models import PasswordSetupToken, User
from .services import UserService


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:editorial_dashboard")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next", "core:editorial_dashboard"))

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("users:login")


# ---------------------------------------------------------------------------
# User list
# ---------------------------------------------------------------------------

@login_required(login_url="users:login")
def user_list(request):
    if not request.user.is_admin():
        messages.error(request, "Only admins can access user management.")
        return redirect("users:login")

    role_filter = request.GET.get("role", "")
    # Ignore unknown role values to avoid leaking info via ORM errors.
    if role_filter and role_filter not in User.Role.values:
        role_filter = ""

    qs = User.objects.all().order_by("-date_joined")
    if role_filter:
        qs = qs.filter(role=role_filter)
    return render(request, "users/user_list.html", {
        "users": qs,
        "roles": User.Role.choices,
        "current_role": role_filter,
    })


# ---------------------------------------------------------------------------
# Create user
# ---------------------------------------------------------------------------

class _FakeForm:
    """Minimal form-like object to pass field errors back to the template."""
    def __init__(self, data=None, errors=None):
        self._data = data or {}
        self._errors = errors or {}

    def __getattr__(self, name):
        class _Field:
            def __init__(self, value, errs):
                self.value = lambda: value
                self.errors = errs
        return _Field(self._data.get(name, ""), self._errors.get(name, []))


@login_required(login_url="users:login")
def create_user(request):
    role_choices = User.Role.choices
    form = _FakeForm()

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        send_email = bool(request.POST.get("send_email"))

        errors = {}
        if not email:
            errors["email"] = ["Email is required."]
        if not role:
            errors["role"] = ["Role is required."]

        if not errors:
            try:
                UserService.create_user(
                    acting_user=request.user,
                    email=email,
                    role=role,
                    first_name=first_name,
                    last_name=last_name,
                    send_email=send_email,
                )
                msg = f"User {email} created."
                if send_email:
                    msg += " A setup email has been sent."
                messages.success(request, msg)
                return redirect("users:user_list")
            except IntegrityError:
                messages.error(request, f"A user with email {email} already exists.")
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
        else:
            form = _FakeForm(
                data={"email": email, "role": role, "first_name": first_name, "last_name": last_name},
                errors=errors,
            )

    return render(request, "users/create_user.html", {
        "form": form,
        "role_choices": role_choices,
    })


# ---------------------------------------------------------------------------
# User detail
# ---------------------------------------------------------------------------

@login_required(login_url="users:login")
def user_detail(request, pk):
    if not request.user.is_admin():
        messages.error(request, "Only admins can view user details.")
        return redirect("users:login")

    profile_user = get_object_or_404(User, pk=pk)
    return render(request, "users/user_detail.html", {
        "profile_user": profile_user,
        "role_choices": User.Role.choices,
    })


# ---------------------------------------------------------------------------
# Update role
# ---------------------------------------------------------------------------

@login_required(login_url="users:login")
def update_role(request, pk):
    if request.method != "POST":
        return redirect("users:user_detail", pk=pk)

    if not request.user.is_admin():
        messages.error(request, "Only admins can change roles.")
        return redirect("users:user_detail", pk=pk)

    profile_user = get_object_or_404(User, pk=pk)
    new_role = request.POST.get("role", "").strip()

    if new_role not in User.Role.values:
        messages.error(request, f"Invalid role '{new_role}'.")
    else:
        profile_user.role = new_role
        profile_user.save(update_fields=["role"])
        messages.success(request, f"Role updated to {profile_user.get_role_display()}.")

    return redirect("users:user_detail", pk=pk)


# ---------------------------------------------------------------------------
# Delete user
# ---------------------------------------------------------------------------

@login_required(login_url="users:login")
def delete_user(request, pk):
    if request.method != "POST":
        return redirect("users:user_detail", pk=pk)

    if not request.user.is_admin():
        messages.error(request, "Only admins can delete users.")
        return redirect("users:user_detail", pk=pk)

    profile_user = get_object_or_404(User, pk=pk)
    email = profile_user.email
    profile_user.delete()
    messages.success(request, f"User {email} deleted.")
    return redirect("users:user_list")


# ---------------------------------------------------------------------------
# Resend setup email
# ---------------------------------------------------------------------------

@login_required(login_url="users:login")
def resend_setup_email(request, pk):
    if request.method != "POST":
        return redirect("users:user_detail", pk=pk)

    profile_user = get_object_or_404(User, pk=pk)
    try:
        UserService.resend_setup_email(acting_user=request.user, target_user=profile_user)
        messages.success(request, f"Setup email resent to {profile_user.email}.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))

    return redirect("users:user_detail", pk=pk)


# ---------------------------------------------------------------------------
# Password setup (token link — no login required)
# ---------------------------------------------------------------------------

def setup_password(request):
    token_str = request.GET.get("token", "")
    valid = PasswordSetupToken.objects.filter(token=token_str, is_used=False).exists()

    if request.method == "POST":
        token_str = request.POST.get("token", "")
        new_password = request.POST.get("new_password", "")
        confirm = request.POST.get("confirm_password", "")

        if new_password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, "users/setup_password.html", {"valid_token": True, "token": token_str})

        try:
            UserService.setup_password(token_str=token_str, new_password=new_password)
            messages.success(request, "Password set successfully! You can now sign in.")
            return redirect("users:login")
        except ValidationError as exc:
            messages.error(request, str(exc))
            return render(request, "users/setup_password.html", {"valid_token": True, "token": token_str})

    return render(request, "users/setup_password.html", {"valid_token": valid, "token": token_str})
