"""Auth URL configuration."""

from django.urls import path

from . import views

app_name = "auth"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("check-session/", views.check_session, name="check_session"),
] 