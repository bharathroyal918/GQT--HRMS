"""Selectors for querying audit logs and compliance oversight data."""
from typing import Optional
from datetime import datetime, time
from django.db.models import QuerySet, Count, Q
from django.utils import timezone
from apps.core.models import AuditLog


def list_audit_logs(
    *,
    search: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> QuerySet[AuditLog]:
    """Retrieve filtered audit logs with related user pre-selected."""
    qs = AuditLog.objects.select_related("user").order_by("-created_at")

    if search:
        search = search.strip()
        qs = qs.filter(
            Q(action__icontains=search)
            | Q(resource_type__icontains=search)
            | Q(resource_id__icontains=search)
            | Q(correlation_id__icontains=search)
            | Q(user__email__icontains=search)
        )

    if action:
        qs = qs.filter(action__iexact=action.strip())

    if resource_type:
        qs = qs.filter(resource_type__iexact=resource_type.strip())

    if user_id:
        qs = qs.filter(user_id=user_id)

    if correlation_id:
        qs = qs.filter(correlation_id=correlation_id.strip())

    if date_from:
        try:
            d_from = datetime.fromisoformat(date_from)
            qs = qs.filter(created_at__gte=d_from)
        except (ValueError, TypeError):
            pass

    if date_to:
        try:
            d_to = datetime.fromisoformat(date_to)
            qs = qs.filter(created_at__lte=d_to)
        except (ValueError, TypeError):
            pass

    return qs


def get_audit_summary() -> dict:
    """Retrieve high-level summary statistics for compliance oversight."""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_count = AuditLog.objects.count()
    today_count = AuditLog.objects.filter(created_at__gte=today_start).count()
    unique_actors = AuditLog.objects.exclude(user=None).values("user").distinct().count()
    unique_resource_types = AuditLog.objects.values("resource_type").distinct().count()

    top_actions = list(
        AuditLog.objects.values("action")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    recent_critical_actions = list(
        AuditLog.objects.filter(
            Q(action__icontains="APPROVE")
            | Q(action__icontains="REJECT")
            | Q(action__icontains="DELETE")
            | Q(action__icontains="SECURITY")
            | Q(action__icontains="FAIL")
        )
        .values("action")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    return {
        "total_count": total_count,
        "today_count": today_count,
        "unique_actors": unique_actors,
        "unique_resource_types": unique_resource_types,
        "top_actions": top_actions,
        "recent_critical_actions": recent_critical_actions,
    }

