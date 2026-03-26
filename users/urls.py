from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.user_list, name="user_list"),
    path("new/", views.create_user, name="create_user"),
    path("<int:pk>/", views.user_detail, name="user_detail"),
    path("<int:pk>/role/", views.update_role, name="update_role"),
    path("<int:pk>/delete/", views.delete_user, name="delete_user"),
    path("<int:pk>/resend/", views.resend_setup_email, name="resend_email"),
    path("setup-password/", views.setup_password, name="setup_password"),
]
