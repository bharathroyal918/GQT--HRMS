"""Selectors for Job Requirements, Verification Checks, and Workflow Metrics.

Encapsulates database queries, filtering, full-text search, and relational prefetching.
"""
from typing import Any, Dict, Optional
from uuid import UUID
from django.db.models import Q, QuerySet, Count
from django.shortcuts import get_object_or_404
from apps.jobs.models import (
    JobRequirement,
    JobStatusChoices,
    JobVerificationCheck,
    CheckStatusChoices,
)


def list_jobs(*, filters: Optional[Dict[str, Any]] = None) -> QuerySet[JobRequirement]:
    """Retrieves paginated job requirements with optimized joins and filtering."""
    filters = filters or {}
    qs = JobRequirement.objects.select_related(
        "company",
        "submitted_by",
        "assigned_verifier",
        "approved_by",
        "rejected_by",
    ).prefetch_related(
        "verification_checks",
        "verification_checks__verified_by",
    )

    search = filters.get("search")
    if search:
        search_term = str(search).strip()
        qs = qs.filter(
            Q(title__icontains=search_term)
            | Q(company__name__icontains=search_term)
            | Q(job_location__icontains=search_term)
            | Q(description__icontains=search_term)
        )

    status = filters.get("status")
    if status:
        qs = qs.filter(status=status)

    role_category = filters.get("role_category")
    if role_category:
        qs = qs.filter(role_category=role_category)

    company_id = filters.get("company_id")
    if company_id:
        qs = qs.filter(company_id=company_id)

    work_arrangement = filters.get("work_arrangement")
    if work_arrangement:
        qs = qs.filter(work_arrangement=work_arrangement)

    has_bond = filters.get("has_bond")
    if has_bond is not None:
        qs = qs.filter(has_bond=bool(has_bond))

    min_ctc = filters.get("min_ctc")
    if min_ctc:
        qs = qs.filter(max_ctc_lpa__gte=min_ctc)

    submitted_by = filters.get("submitted_by")
    if submitted_by:
        qs = qs.filter(submitted_by_id=submitted_by)

    assigned_verifier = filters.get("assigned_verifier")
    if assigned_verifier:
        qs = qs.filter(assigned_verifier_id=assigned_verifier)

    return qs.order_by("-created_at")


def get_job_by_id(job_id: str | UUID) -> JobRequirement:
    """Retrieves a single JobRequirement with all relations prefetched."""
    return get_object_or_404(
        JobRequirement.objects.select_related(
            "company",
            "submitted_by",
            "assigned_verifier",
            "approved_by",
            "rejected_by",
        ).prefetch_related(
            "verification_checks",
            "verification_checks__verified_by",
            "workflow_history",
            "workflow_history__actor",
        ),
        id=job_id,
    )


def list_verification_queue() -> QuerySet[JobRequirement]:
    """Retrieves jobs awaiting or currently undergoing the 5-point verification review."""
    return (
        JobRequirement.objects.filter(
            status__in=[
                JobStatusChoices.PENDING_VERIFICATION,
                JobStatusChoices.UNDER_VERIFICATION,
            ]
        )
        .select_related("company", "submitted_by", "assigned_verifier")
        .prefetch_related("verification_checks", "verification_checks__verified_by")
        .order_by("registration_deadline", "-created_at")
    )


def list_approval_queue() -> QuerySet[JobRequirement]:
    """Retrieves jobs with all 5 checks passed awaiting Placement Head sign-off."""
    return (
        JobRequirement.objects.filter(status=JobStatusChoices.PENDING_APPROVAL)
        .select_related("company", "submitted_by", "assigned_verifier")
        .prefetch_related("verification_checks", "verification_checks__verified_by")
        .order_by("registration_deadline", "-created_at")
    )


def get_job_workflow_metrics() -> Dict[str, Any]:
    """Calculates aggregate metrics and workflow statistics based on real persisted data."""
    status_counts = dict(
        JobRequirement.objects.values("status")
        .annotate(total=Count("id"))
        .values_list("status", "total")
    )

    check_counts = dict(
        JobVerificationCheck.objects.values("status")
        .annotate(total=Count("id"))
        .values_list("status", "total")
    )

    total_jobs = JobRequirement.objects.count()

    return {
        "total_jobs": total_jobs,
        "draft_jobs": status_counts.get(JobStatusChoices.DRAFT, 0),
        "pending_verification_jobs": status_counts.get(JobStatusChoices.PENDING_VERIFICATION, 0),
        "under_verification_jobs": status_counts.get(JobStatusChoices.UNDER_VERIFICATION, 0),
        "changes_requested_jobs": status_counts.get(JobStatusChoices.CHANGES_REQUESTED, 0),
        "pending_approval_jobs": status_counts.get(JobStatusChoices.PENDING_APPROVAL, 0),
        "approved_jobs": status_counts.get(JobStatusChoices.APPROVED, 0),
        "rejected_jobs": status_counts.get(JobStatusChoices.REJECTED, 0),
        "verification_stats": {
            "total_checks": sum(check_counts.values()),
            "verified_checks": check_counts.get(CheckStatusChoices.VERIFIED, 0),
            "pending_checks": check_counts.get(CheckStatusChoices.PENDING, 0),
            "flagged_checks": check_counts.get(CheckStatusChoices.FLAGGED, 0),
            "rejected_checks": check_counts.get(CheckStatusChoices.REJECTED, 0),
        },
    }

