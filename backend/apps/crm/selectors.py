"""Recruitment CRM Query Selectors.

Encapsulates data retrieval, query optimization (select_related / prefetch_related),
search filters, and sorting.
"""
from typing import Optional
from django.db.models import QuerySet, Q, Count
from django.utils import timezone
from apps.crm.models import (
    Company,
    HRContact,
    OutreachActivity,
    FollowUp,
    FollowUpStatusChoices,
)


def list_companies(
    *,
    search: Optional[str] = None,
    status: Optional[str] = None,
    industry: Optional[str] = None,
    source: Optional[str] = None,
    tier: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    include_deleted: bool = False,
) -> QuerySet[Company]:
    """Retrieves filtered companies with pre-annotated contact & activity counts."""
    qs = Company.objects.select_related("assigned_to", "created_by").annotate(
        contacts_count=Count("contacts", filter=Q(contacts__is_deleted=False), distinct=True),
        outreach_count=Count("outreach_activities", filter=Q(outreach_activities__is_deleted=False), distinct=True),
        pending_followups_count=Count(
            "follow_ups",
            filter=Q(follow_ups__status=FollowUpStatusChoices.PENDING, follow_ups__is_deleted=False),
            distinct=True,
        ),
    )

    if not include_deleted:
        qs = qs.filter(is_deleted=False)

    if status:
        qs = qs.filter(status=status)

    if industry:
        qs = qs.filter(industry=industry)

    if source:
        qs = qs.filter(source=source)

    if tier:
        qs = qs.filter(tier=tier)

    if assigned_to_id:
        qs = qs.filter(assigned_to_id=assigned_to_id)

    if search:
        search_term = search.strip()
        qs = qs.filter(
            Q(name__icontains=search_term)
            | Q(canonical_domain__icontains=search_term)
            | Q(website__icontains=search_term)
            | Q(notes__icontains=search_term)
        )

    return qs.order_by("-created_at")


def get_company_by_id(company_id: str) -> Optional[Company]:
    """Retrieves full company detail with prefetched relationships."""
    try:
        return (
            Company.objects.select_related("assigned_to", "created_by", "updated_by")
            .prefetch_related(
                "contacts",
                "outreach_activities__executive",
                "outreach_activities__contact",
                "follow_ups__assigned_to",
                "follow_ups__contact",
            )
            .get(id=company_id, is_deleted=False)
        )
    except Company.DoesNotExist:
        return None


def list_hr_contacts(
    *,
    company_id: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> QuerySet[HRContact]:
    """Retrieves HR contacts for a specific company or directory-wide."""
    qs = HRContact.objects.select_related("company", "assigned_to", "created_by").filter(
        is_deleted=False
    )

    if company_id:
        qs = qs.filter(company_id=company_id)

    if status:
        qs = qs.filter(status=status)

    if search:
        term = search.strip()
        qs = qs.filter(
            Q(name__icontains=term)
            | Q(email__icontains=term)
            | Q(phone__icontains=term)
            | Q(designation__icontains=term)
            | Q(company__name__icontains=term)
        )

    return qs.order_by("-is_primary", "-created_at")


def list_outreach_activities(
    *,
    company_id: Optional[str] = None,
    executive_id: Optional[str] = None,
    channel: Optional[str] = None,
    outcome: Optional[str] = None,
) -> QuerySet[OutreachActivity]:
    """Retrieves outreach activity touchpoints with executive details."""
    qs = OutreachActivity.objects.select_related("company", "contact", "executive").filter(
        is_deleted=False
    )

    if company_id:
        qs = qs.filter(company_id=company_id)

    if executive_id:
        qs = qs.filter(executive_id=executive_id)

    if channel:
        qs = qs.filter(channel=channel)

    if outcome:
        qs = qs.filter(outcome=outcome)

    return qs.order_by("-attempted_at")


def list_follow_ups(
    *,
    assigned_to_id: Optional[str] = None,
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    filter_type: Optional[str] = None,  # "due_today", "overdue", "upcoming"
) -> QuerySet[FollowUp]:
    """Retrieves actionable follow-up tasks with state filters."""
    qs = FollowUp.objects.select_related("company", "contact", "assigned_to", "completed_by").filter(
        is_deleted=False
    )

    if assigned_to_id:
        qs = qs.filter(assigned_to_id=assigned_to_id)

    if company_id:
        qs = qs.filter(company_id=company_id)

    if status:
        qs = qs.filter(status=status)

    now = timezone.now()
    today = timezone.localdate()

    if filter_type == "overdue":
        qs = qs.filter(
            status=FollowUpStatusChoices.PENDING,
            due_date__lt=now,
        )
    elif filter_type == "due_today":
        start_of_today = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        end_of_today = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.max.time())
        )
        qs = qs.filter(
            status=FollowUpStatusChoices.PENDING,
            due_date__gte=start_of_today,
            due_date__lte=end_of_today,
        )
    elif filter_type == "upcoming":
        qs = qs.filter(
            status=FollowUpStatusChoices.PENDING,
            due_date__gt=now,
        )

    return qs.order_by("due_date", "-priority")

