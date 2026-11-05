"""Serializers for Audit Logs and Compliance Views."""
from rest_framework import serializers
from apps.core.models import AuditLog


class AuditUserSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "user_agent",
            "changes",
            "correlation_id",
            "created_at",
        ]
        read_only_fields = fields

    def get_user(self, obj: AuditLog):
        if not obj.user:
            return None
        return {
            "id": str(obj.user.id),
            "email": obj.user.email,
            "full_name": getattr(obj.user, "full_name", "") or obj.user.email,
        }


class AuditSummarySerializer(serializers.Serializer):
    total_count = serializers.IntegerField()
    today_count = serializers.IntegerField()
    unique_actors = serializers.IntegerField()
    unique_resource_types = serializers.IntegerField()
    top_actions = serializers.ListField(child=serializers.DictField())
    recent_critical_actions = serializers.ListField(child=serializers.DictField())

