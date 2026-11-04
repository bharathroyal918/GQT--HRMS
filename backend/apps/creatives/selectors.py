"""Query Selector Layer for Creative Studio.

Read-only, high-performance querysets using select_related, prefetch_related,
and role-scoped operational views.
"""
from typing import Any, Dict, Optional
from uuid import UUID
from django.db.models import Count, Q, QuerySet
from apps.accounts.models import User, RoleCatalog
from apps.creatives.models import (
    CreativeRequest,
    CreativeAssetVersion,
    CreativeStatusChoices,
    VersionStatusChoices,
    ComplianceCheckStatusChoices,
)


def list_creative_requests(
    user: User,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    creative_type: Optional[str] = None,
    assigned_to: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[CreativeRequest]:
    """Retrieve creative requisitions with role-aware visibility and filters."""
    qs = CreativeRequest.objects.select_related(
        "job_requirement",
        "company",
        "created_by",
        "assigned_designer",
        "active_version",
    ).prefetch_related("versions", "history")

    user_roles = set(user.get_roles())
    is_privileged = bool(
        user_roles
        & {
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.CREATIVE_REVIEWER,
            RoleCatalog.AUDITOR,
        }
        or user.is_superuser
    )

    # Scoped visibility: if purely designer, restrict to assigned or created
    if not is_privileged:
        if RoleCatalog.CREATIVE_DESIGNER in user_roles:
            qs = qs.filter(Q(assigned_designer=user) | Q(created_by=user))
        elif RoleCatalog.PLACEMENT_OFFICER in user_roles:
            qs = qs.filter(Q(created_by=user) | Q(status__in=[
                CreativeStatusChoices.APPROVED,
                CreativeStatusChoices.READY_FOR_HANDOFF,
            ]))

    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if creative_type:
        qs = qs.filter(creative_type=creative_type)
    if assigned_to:
        qs = qs.filter(assigned_designer_id=assigned_to)
    if search:
        search_term = search.strip()
        qs = qs.filter(
            Q(title__icontains=search_term)
            | Q(request_code__icontains=search_term)
            | Q(brief__icontains=search_term)
            | Q(company__name__icontains=search_term)
            | Q(job_requirement__title__icontains=search_term)
        )

    return qs.distinct()


def get_creative_request_by_id(request_id: UUID | str) -> Optional[CreativeRequest]:
    """Fetch complete creative requisition detail with preloaded versions and checklist."""
    try:
        return (
            CreativeRequest.objects.select_related(
                "job_requirement",
                "company",
                "created_by",
                "assigned_designer",
                "active_version",
            )
            .prefetch_related(
                "versions__compliance_checks",
                "versions__uploader",
                "versions__reviewed_by",
                "history__actor",
            )
            .get(id=request_id)
        )
    except CreativeRequest.DoesNotExist:
        return None


def get_asset_version_by_id(version_id: UUID | str) -> Optional[CreativeAssetVersion]:
    """Fetch a specific asset version with request and compliance checks."""
    try:
        return (
            CreativeAssetVersion.objects.select_related(
                "request",
                "uploader",
                "reviewed_by",
                "request__job_requirement",
                "request__company",
            )
            .prefetch_related("compliance_checks__verified_by")
            .get(id=version_id)
        )
    except CreativeAssetVersion.DoesNotExist:
        return None


def list_triage_queue() -> QuerySet[CreativeRequest]:
    """Requisitions in SUBMITTED state awaiting review and designer assignment."""
    return (
        CreativeRequest.objects.filter(status=CreativeStatusChoices.SUBMITTED)
        .select_related("job_requirement", "company", "created_by")
        .order_by("-priority", "target_completion_date", "-created_at")
    )


def list_designer_queue(designer_user: User) -> QuerySet[CreativeRequest]:
    """Active requisitions assigned to the given designer."""
    return (
        CreativeRequest.objects.filter(
            assigned_designer=designer_user,
            status__in=[
                CreativeStatusChoices.ASSIGNED,
                CreativeStatusChoices.IN_DESIGN,
                CreativeStatusChoices.CHANGES_REQUESTED,
            ],
        )
        .select_related("job_requirement", "company", "created_by", "active_version")
        .order_by("-priority", "target_completion_date")
    )


def list_review_queue() -> QuerySet[CreativeAssetVersion]:
    """Asset versions submitted for formal review awaiting compliance evaluation."""
    return (
        CreativeAssetVersion.objects.filter(
            status=VersionStatusChoices.SUBMITTED_FOR_REVIEW
        )
        .select_related("request", "request__company", "uploader")
        .prefetch_related("compliance_checks")
        .order_by("created_at")
    )


def list_handoff_queue() -> QuerySet[CreativeRequest]:
    """Approved requisitions ready for campus drive / student publishing."""
    return (
        CreativeRequest.objects.filter(status=CreativeStatusChoices.APPROVED)
        .select_related("job_requirement", "company", "created_by", "active_version")
        .order_by("-updated_at")
    )


def get_creative_studio_metrics() -> Dict[str, Any]:
    """Aggregates operational metrics for the Creative Studio dashboard."""
    status_counts = CreativeRequest.objects.values("status").annotate(
        count=Count("id")
    )
    counts_map = {item["status"]: item["count"] for item in status_counts}

    total_requests = CreativeRequest.objects.count()
    triage_count = counts_map.get(CreativeStatusChoices.SUBMITTED, 0)
    in_design_count = (
        counts_map.get(CreativeStatusChoices.ASSIGNED, 0)
        + counts_map.get(CreativeStatusChoices.IN_DESIGN, 0)
        + counts_map.get(CreativeStatusChoices.CHANGES_REQUESTED, 0)
    )
    in_review_count = counts_map.get(CreativeStatusChoices.IN_REVIEW, 0)
    approved_count = counts_map.get(CreativeStatusChoices.APPROVED, 0)
    ready_handoff_count = counts_map.get(CreativeStatusChoices.READY_FOR_HANDOFF, 0)

    # Asset Versions count
    total_versions = CreativeAssetVersion.objects.count()
    pending_versions_review = CreativeAssetVersion.objects.filter(
        status=VersionStatusChoices.SUBMITTED_FOR_REVIEW
    ).count()

    return {
        "total_requests": total_requests,
        "triage_queue_count": triage_count,
        "in_design_count": in_design_count,
        "in_review_count": in_review_count,
        "approved_count": approved_count,
        "ready_for_handoff_count": ready_handoff_count,
        "total_asset_versions": total_versions,
        "pending_versions_review": pending_versions_review,
    }
