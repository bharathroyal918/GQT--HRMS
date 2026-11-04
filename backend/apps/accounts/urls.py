"""Accounts URL routing configuration."""
from django.urls import path
from apps.accounts.views import (
    LoginAPIView,
    LogoutAPIView,
    TokenRefreshAPIView,
    CurrentUserProfileAPIView,
    UserManagementListCreateAPIView,
    UserDetailAPIView,
    UserRoleAssignmentAPIView,
)

app_name = "accounts"

urlpatterns = [
    # Session / Token Lifecycle
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("me/", CurrentUserProfileAPIView.as_view(), name="current-user"),

    # User Management (Admin / Superuser only)
    path("users/", UserManagementListCreateAPIView.as_view(), name="user-list-create"),
    path("users/<uuid:user_id>/", UserDetailAPIView.as_view(), name="user-detail"),
    path("users/<uuid:user_id>/roles/", UserRoleAssignmentAPIView.as_view(), name="user-roles"),
]
