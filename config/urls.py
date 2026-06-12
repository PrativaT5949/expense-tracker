"""Top-level URL configuration for the Expense Tracker project."""
from django.contrib import admin
from django.urls import path, include
from expenses.views import register_user, login_user

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/", register_user, name="register"),
    path("api/auth/login/", login_user, name="login"),
    path("api/", include("expenses.urls")),
]