"""Authentication and Identity REST API Views."""
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status, permissions, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.accounts.serializers import (
    LoginInputSerializer,
    UserProfileSerializer,
    UserProvisionSerializer,
    RoleAssignmentInputSerializer,
)
from apps.accounts.services import (
    create_user,
    generate_jwt_tokens_for_user,
    assign_role,
    revoke_role,
    set_user_active_status,
)
from apps.accounts.selectors import list_users, get_user_by_id
from apps.accounts.permissions import IsAdminOrSuperUser
from apps.accounts.throttles import AuthLoginRateThrottle
from apps.core.models import AuditLog
from apps.core.middleware import get_current_correlation_id


class LoginAPIView(APIView):
    """Authenticates staff credentials, issues SimpleJWT tokens, and sets secure HttpOnly cookies."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthLoginRateThrottle]

    @extend_schema(
        summary="User Authentication & Cookie Issuance",
        request=LoginInputSerializer,
        responses={200: UserProfileSerializer, 401: dict},
    )
    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]

        user = authenticate(request, email=email, password=password)
        if not user or not user.is_active:
            # Record failed login attempt in audit log
            AuditLog.objects.create(
                action="AUTH_LOGIN_FAILED",
                resource_type="accounts.User",
                resource_id=email,
                ip_address=request.META.get("REMOTE_ADDR"),
                correlation_id=get_current_correlation_id(),
                changes={"email": email, "reason": "Invalid credentials or inactive account"},
            )
            return Response(
                {"detail": "Invalid credentials or account is deactivated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate token pair
        access_token, refresh_token = generate_jwt_tokens_for_user(user)

        # Record audit success
        AuditLog.objects.create(
            user=user,
            action="AUTH_LOGIN_SUCCESS",
            resource_type="accounts.User",
            resource_id=str(user.id),
            ip_address=request.META.get("REMOTE_ADDR"),
            correlation_id=get_current_correlation_id(),
        )

        response = Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

        # Set secure HttpOnly cookies
        cookie_secure = getattr(settings, "AUTH_COOKIE_SECURE", False)
        cookie_samesite = getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax")
        access_cookie_name = getattr(settings, "AUTH_COOKIE_ACCESS", "gqt_access_token")
        refresh_cookie_name = getattr(settings, "AUTH_COOKIE_REFRESH", "gqt_refresh_token")

        response.set_cookie(
            key=access_cookie_name,
            value=access_token,
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=15 * 60,
            path="/",
        )
        response.set_cookie(
            key=refresh_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=7 * 24 * 60 * 60,
            path="/",
        )

        return response


class LogoutAPIView(APIView):
    """Terminates session, blacklists refresh token, and purges HttpOnly authentication cookies."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="User Session Invalidation & Logout",
        request=None,
        responses={200: inline_serializer("LogoutSuccessResponse", fields={"detail": serializers.CharField()})},
    )
    def post(self, request):
        refresh_cookie_name = getattr(settings, "AUTH_COOKIE_REFRESH", "gqt_refresh_token")
        raw_refresh = request.COOKIES.get(refresh_cookie_name) or request.data.get("refresh")

        if raw_refresh:
            try:
                token = RefreshToken(raw_refresh)
                token.blacklist()
            except TokenError:
                pass

        if request.user and request.user.is_authenticated:
            AuditLog.objects.create(
                user=request.user,
                action="AUTH_LOGOUT",
                resource_type="accounts.User",
                resource_id=str(request.user.id),
                ip_address=request.META.get("REMOTE_ADDR"),
                correlation_id=get_current_correlation_id(),
            )

        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        access_cookie_name = getattr(settings, "AUTH_COOKIE_ACCESS", "gqt_access_token")

        response.delete_cookie(access_cookie_name, path="/")
        response.delete_cookie(refresh_cookie_name, path="/")
        return response


class TokenRefreshAPIView(APIView):
    """Refreshes access token via HttpOnly refresh cookie."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Silent Token Refresh",
        request=None,
        responses={
            200: inline_serializer("TokenRefreshSuccessResponse", fields={"detail": serializers.CharField()}),
            401: inline_serializer("TokenRefreshErrorResponse", fields={"detail": serializers.CharField()}),
        },
    )
    def post(self, request):
        refresh_cookie_name = getattr(settings, "AUTH_COOKIE_REFRESH", "gqt_refresh_token")
        raw_refresh = request.COOKIES.get(refresh_cookie_name) or request.data.get("refresh")

        if not raw_refresh:
            return Response(
                {"detail": "Refresh token cookie missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(raw_refresh)
            new_access_token = str(refresh.access_token)
        except TokenError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({"detail": "Token refreshed successfully."}, status=status.HTTP_200_OK)
        cookie_secure = getattr(settings, "AUTH_COOKIE_SECURE", False)
        cookie_samesite = getattr(settings, "AUTH_COOKIE_SAMESITE", "Lax")
        access_cookie_name = getattr(settings, "AUTH_COOKIE_ACCESS", "gqt_access_token")

        response.set_cookie(
            key=access_cookie_name,
            value=new_access_token,
            httponly=True,
            secure=cookie_secure,
            samesite=cookie_samesite,
            max_age=15 * 60,
            path="/",
        )
        return response


class CurrentUserProfileAPIView(APIView):
    """Returns the profile and role assignments of the currently authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Retrieve Current User Profile", responses={200: UserProfileSerializer})
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class UserManagementListCreateAPIView(APIView):
    """Administrative directory of staff accounts and staff creation gate."""

    permission_classes = [IsAdminOrSuperUser]

    @extend_schema(summary="List Staff Accounts", responses={200: UserProfileSerializer(many=True)})
    def get(self, request):
        search = request.query_params.get("search")
        role_code = request.query_params.get("role")
        is_active = None
        if "is_active" in request.query_params:
            is_active = request.query_params.get("is_active").lower() in ("true", "1")

        users = list_users(search=search, role_code=role_code, is_active=is_active)
        return Response(UserProfileSerializer(users, many=True).data)

    @extend_schema(
        summary="Provision New Staff Account",
        request=UserProvisionSerializer,
        responses={201: UserProfileSerializer},
    )
    def post(self, request):
        serializer = UserProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = create_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
            phone_number=serializer.validated_data.get("phone_number", ""),
            role_codes=serializer.validated_data.get("roles", []),
            is_staff=serializer.validated_data.get("is_staff", False),
            created_by=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailAPIView(APIView):
    """Administrative retrieval and status updates for a specific user."""

    permission_classes = [IsAdminOrSuperUser]

    @extend_schema(
        summary="Retrieve Staff Account Details",
        responses={
            200: UserProfileSerializer,
            404: inline_serializer("UserNotFoundResponse", fields={"detail": serializers.CharField()}),
        },
    )
    def get(self, request, user_id):
        user = get_user_by_id(user_id)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserProfileSerializer(user).data)

    @extend_schema(
        summary="Update Staff Account Active Status",
        request=inline_serializer("UserStatusUpdateInput", fields={"is_active": serializers.BooleanField()}),
        responses={
            200: UserProfileSerializer,
            404: inline_serializer("UserNotFoundResponsePatch", fields={"detail": serializers.CharField()}),
        },
    )
    def patch(self, request, user_id):
        user = get_user_by_id(user_id)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if "is_active" in request.data:
            set_user_active_status(
                user=user,
                is_active=bool(request.data["is_active"]),
                updated_by=request.user,
                ip_address=request.META.get("REMOTE_ADDR"),
            )

        return Response(UserProfileSerializer(user).data)


class UserRoleAssignmentAPIView(APIView):
    """Assign or revoke an operational role for a user."""

    permission_classes = [IsAdminOrSuperUser]

    @extend_schema(
        summary="Assign Role to Staff Account",
        request=RoleAssignmentInputSerializer,
        responses={
            200: UserProfileSerializer,
            404: inline_serializer("UserNotFoundRoleAssign", fields={"detail": serializers.CharField()}),
        },
    )
    def post(self, request, user_id):
        user = get_user_by_id(user_id)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleAssignmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assign_role(
            user=user,
            role_code=serializer.validated_data["role_code"],
            assigned_by=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Revoke Role from Staff Account",
        request=RoleAssignmentInputSerializer,
        responses={
            200: UserProfileSerializer,
            404: inline_serializer("UserNotFoundRoleRevoke", fields={"detail": serializers.CharField()}),
        },
    )
    def delete(self, request, user_id):
        user = get_user_by_id(user_id)
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleAssignmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        revoke_role(
            user=user,
            role_code=serializer.validated_data["role_code"],
            revoked_by=request.user,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(UserProfileSerializer(user).data, status=status.HTTP_200_OK)
