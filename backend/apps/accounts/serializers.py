"""DRF Serializers for Accounts & Authentication."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.accounts.models import User, Role, RoleCatalog


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for role representation."""

    class Meta:
        model = Role
        fields = ["id", "code", "name", "description"]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile representation."""

    roles = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone_number",
            "is_active",
            "is_staff",
            "is_superuser",
            "roles",
            "created_at",
        ]
        read_only_fields = ["id", "is_superuser", "created_at"]

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_roles(self, obj: User):
        return obj.get_roles()


class LoginInputSerializer(serializers.Serializer):
    """Input serializer for email/password authentication."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={"input_type": "password"})


class UserProvisionSerializer(serializers.Serializer):
    """Input serializer for administrative staff creation."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=10, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    phone_number = serializers.CharField(required=False, allow_blank=True, default="")
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=RoleCatalog.CHOICES),
        required=False,
        default=list,
    )
    is_staff = serializers.BooleanField(required=False, default=False)


class RoleAssignmentInputSerializer(serializers.Serializer):
    """Input serializer for role assignment/revocation."""

    role_code = serializers.ChoiceField(choices=RoleCatalog.CHOICES, required=True)
