"""Recruitment CRM Domain Services.

Encapsulates transactional write operations, duplicate detection, automated state progression,
and immutable audit logging.
"""
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.core.middleware import get_current_correlation_id
from apps.crm.models import (
    Company,
    HRContact,
    OutreachActivity,
    FollowUp,
    CompanyStatusChoices,
    FollowUpStatusChoices,
    FollowUpPriorityChoices,
    OutreachOutcomeChoices,
    extract_canonical_domain,
    normalize_company_name,
)


def detect_company_duplicates(
    name: str,
    website: str = "",
    exclude_company_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyzes proposed company name and website against existing database records.

    Does NOT automatically merge or delete records. Returns diagnostic match list.
    """
    normalized = normalize_company_name(name)
    domain = extract_canonical_domain(website) if website else ""

    matches: List[Dict[str, Any]] = []

    base_qs = Company.objects.filter(is_deleted=False)
    if exclude_company_id:
        base_qs = base_qs.exclude(id=exclude_company_id)

    # 1. Exact Canonical Domain Match
    if domain:
        domain_matches = base_qs.filter(canonical_domain__iexact=domain)
        for comp in domain_matches:
            matches.append({
                "id": str(comp.id),
                "name": comp.name,
                "canonical_domain": comp.canonical_domain,
                "status": comp.status,
                "match_reason": "EXACT_DOMAIN_MATCH",
            })

    # 2. Normalized Name Match
    if normalized:
        name_matches = base_qs.filter(normalized_name=normalized)
        for comp in name_matches:
            if not any(m["id"] == str(comp.id) for m in matches):
                matches.append({
                    "id": str(comp.id),
                    "name": comp.name,
                    "canonical_domain": comp.canonical_domain,
                    "status": comp.status,
                    "match_reason": "NORMALIZED_NAME_MATCH",
                })

    return {
        "is_duplicate": len(matches) > 0,
        "match_count": len(matches),
        "matches": matches,
    }


@transaction.atomic
def create_company(
    *,
    name: str,
    website: str = "",
    industry: str = "",
    source: str = "",
    status: str = CompanyStatusChoices.LEAD,
    tier: str = "",
    assigned_to: Optional[User] = None,
    notes: str = "",
    user: Optional[User] = None,
    allow_duplicate: bool = False,
) -> Company:
    """Creates a new Company entity with audit logging and duplicate guard."""
    dup_report = detect_company_duplicates(name=name, website=website)
    if dup_report["is_duplicate"] and not allow_duplicate:
        # If there is an exact domain match or exact name match, reject creation unless overridden
        exact_domains = [m for m in dup_report["matches"] if m["match_reason"] == "EXACT_DOMAIN_MATCH"]
        if exact_domains:
            raise ValidationError(
                f"A company with canonical domain '{exact_domains[0]['canonical_domain']}' already exists: {exact_domains[0]['name']}."
            )
        exact_names = [m for m in dup_report["matches"] if m["match_reason"] == "NORMALIZED_NAME_EXACT_MATCH"]
        if exact_names:
            raise ValidationError(
                f"A company with normalized name '{exact_names[0]['name']}' already exists."
            )

    company = Company(
        name=name.strip(),
        website=website.strip(),
        industry=industry or Company._meta.get_field("industry").default,
        source=source or Company._meta.get_field("source").default,
        status=status or CompanyStatusChoices.LEAD,
        tier=tier or Company._meta.get_field("tier").default,
        assigned_to=assigned_to,
        notes=notes.strip(),
        created_by=user,
        updated_by=user,
    )
    company.save()

    AuditLog.objects.create(
        user=user,
        action="COMPANY_CREATED",
        resource_type="crm.Company",
        resource_id=str(company.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "name": company.name,
            "status": company.status,
            "assigned_to": str(assigned_to.id) if assigned_to else None,
            "canonical_domain": company.canonical_domain,
        },
    )

    return company


@transaction.atomic
def update_company(
    *,
    company: Company,
    user: Optional[User] = None,
    **fields,
) -> Company:
    """Updates company details with delta audit tracking."""
    changes: Dict[str, Any] = {}

    updatable = [
        "name",
        "website",
        "industry",
        "source",
        "status",
        "tier",
        "assigned_to",
        "notes",
    ]

    for key, value in fields.items():
        if key in updatable and hasattr(company, key):
            old_val = getattr(company, key)
            if old_val != value:
                changes[key] = {
                    "old": str(old_val) if old_val is not None else None,
                    "new": str(value) if value is not None else None,
                }
                setattr(company, key, value)

    if changes:
        company.updated_by = user
        company.save()

        AuditLog.objects.create(
            user=user,
            action="COMPANY_UPDATED",
            resource_type="crm.Company",
            resource_id=str(company.id),
            correlation_id=get_current_correlation_id(),
            changes=changes,
        )

    return company


@transaction.atomic
@transaction.atomic
def create_hr_contact(
    *,
    company: Company,
    name: str,
    designation: str = "",
    department: str = "",
    email: str = "",
    phone: str = "",
    alternate_phone: str = "",
    linkedin_url: str = "",
    preferred_channel: str = "",
    is_primary: bool = False,
    notes: str = "",
    assigned_to: Optional[User] = None,
    user: Optional[User] = None,
) -> HRContact:
    """Creates an HR contact for a company, ensuring only one primary contact at a time with row lock."""
    # Acquire lock on company to prevent concurrent primary contact creation race
    Company.objects.select_for_update().filter(id=company.id).exists()

    if is_primary:
        # Demote existing primary contacts
        company.contacts.filter(is_primary=True).update(is_primary=False)

    contact = HRContact(
        company=company,
        name=name.strip(),
        designation=designation.strip(),
        department=department.strip(),
        email=email.strip().lower(),
        phone=phone.strip(),
        alternate_phone=alternate_phone.strip(),
        linkedin_url=linkedin_url.strip(),
        preferred_channel=preferred_channel or HRContact._meta.get_field("preferred_channel").default,
        is_primary=is_primary,
        notes=notes.strip(),
        assigned_to=assigned_to,
        created_by=user,
        updated_by=user,
    )
    contact.save()

    AuditLog.objects.create(
        user=user,
        action="HR_CONTACT_CREATED",
        resource_type="crm.HRContact",
        resource_id=str(contact.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "company_id": str(company.id),
            "name": contact.name,
            "email": contact.email,
            "is_primary": contact.is_primary,
        },
    )

    return contact


@transaction.atomic
def update_hr_contact(
    *,
    contact: HRContact,
    user: Optional[User] = None,
    **fields,
) -> HRContact:
    """Updates HR Contact record with primary toggle handling and audit logging."""
    changes: Dict[str, Any] = {}

    if fields.get("is_primary") is True and not contact.is_primary:
        contact.company.contacts.filter(is_primary=True).exclude(id=contact.id).update(is_primary=False)

    updatable = [
        "name",
        "designation",
        "department",
        "email",
        "phone",
        "alternate_phone",
        "linkedin_url",
        "preferred_channel",
        "status",
        "is_primary",
        "notes",
        "assigned_to",
    ]

    for key, value in fields.items():
        if key in updatable and hasattr(contact, key):
            old_val = getattr(contact, key)
            if old_val != value:
                changes[key] = {
                    "old": str(old_val) if old_val is not None else None,
                    "new": str(value) if value is not None else None,
                }
                setattr(contact, key, value)

    if changes:
        contact.updated_by = user
        contact.save()

        AuditLog.objects.create(
            user=user,
            action="HR_CONTACT_UPDATED",
            resource_type="crm.HRContact",
            resource_id=str(contact.id),
            correlation_id=get_current_correlation_id(),
            changes=changes,
        )

    return contact


@transaction.atomic
def log_outreach_activity(
    *,
    company: Company,
    executive: User,
    channel: str,
    outcome: str,
    notes: str,
    contact: Optional[HRContact] = None,
    next_action: str = "",
    follow_up_date: Optional[timezone.datetime] = None,
) -> OutreachActivity:
    """Logs an outreach touchpoint and advances company status if positive response received."""
    if not notes.strip():
        raise ValidationError("Outreach notes are required.")

    activity = OutreachActivity(
        company=company,
        contact=contact,
        executive=executive,
        attempted_at=timezone.now(),
        channel=channel,
        outcome=outcome,
        notes=notes.strip(),
        next_action=next_action.strip(),
        follow_up_date=follow_up_date,
    )
    activity.save()

    # Dynamic status advancement based on outcome
    status_changed = False
    old_status = company.status

    if outcome in [OutreachOutcomeChoices.INTERESTED, OutreachOutcomeChoices.REQUIREMENT_SHARED]:
        if company.status in [CompanyStatusChoices.LEAD, CompanyStatusChoices.CONTACTED]:
            company.status = CompanyStatusChoices.ENGAGED
            company.save(update_fields=["status", "updated_at"])
            status_changed = True
    elif outcome in [OutreachOutcomeChoices.MEETING_SCHEDULED]:
        if company.status in [CompanyStatusChoices.LEAD]:
            company.status = CompanyStatusChoices.CONTACTED
            company.save(update_fields=["status", "updated_at"])
            status_changed = True
    elif company.status == CompanyStatusChoices.LEAD:
        company.status = CompanyStatusChoices.CONTACTED
        company.save(update_fields=["status", "updated_at"])
        status_changed = True

    # Audit logging
    AuditLog.objects.create(
        user=executive,
        action="OUTREACH_ACTIVITY_LOGGED",
        resource_type="crm.OutreachActivity",
        resource_id=str(activity.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "company_id": str(company.id),
            "channel": activity.channel,
            "outcome": activity.outcome,
            "status_advanced": status_changed,
            "old_status": old_status if status_changed else None,
            "new_status": company.status if status_changed else None,
        },
    )

    # If follow-up date specified, automatically create a linked FollowUp task
    if follow_up_date:
        create_follow_up(
            company=company,
            assigned_to=executive,
            title=f"Follow-up: {activity.next_action or company.name}",
            due_date=follow_up_date,
            description=f"Auto-scheduled from {activity.channel} outreach: {activity.notes[:100]}",
            contact=contact,
            outreach_activity=activity,
            priority=FollowUpPriorityChoices.MEDIUM,
            user=executive,
        )

    return activity


@transaction.atomic
def create_follow_up(
    *,
    company: Company,
    assigned_to: User,
    title: str,
    due_date: timezone.datetime,
    description: str = "",
    contact: Optional[HRContact] = None,
    outreach_activity: Optional[OutreachActivity] = None,
    priority: str = FollowUpPriorityChoices.MEDIUM,
    user: Optional[User] = None,
) -> FollowUp:
    """Schedules an actionable follow-up task."""
    follow_up = FollowUp(
        company=company,
        contact=contact,
        outreach_activity=outreach_activity,
        assigned_to=assigned_to,
        title=title.strip(),
        description=description.strip(),
        due_date=due_date,
        priority=priority or FollowUpPriorityChoices.MEDIUM,
        status=FollowUpStatusChoices.PENDING,
    )
    follow_up.save()

    AuditLog.objects.create(
        user=user or assigned_to,
        action="FOLLOWUP_SCHEDULED",
        resource_type="crm.FollowUp",
        resource_id=str(follow_up.id),
        correlation_id=get_current_correlation_id(),
        changes={
            "company_id": str(company.id),
            "assigned_to": str(assigned_to.id),
            "due_date": follow_up.due_date.isoformat(),
            "priority": follow_up.priority,
        },
    )

    return follow_up


@transaction.atomic
def complete_follow_up(
    *,
    follow_up: FollowUp,
    user: User,
    notes: str = "",
) -> FollowUp:
    """Marks a follow-up as completed with audit attribution."""
    follow_up.status = FollowUpStatusChoices.COMPLETED
    follow_up.completed_at = timezone.now()
    follow_up.completed_by = user
    if notes:
        follow_up.description = f"{follow_up.description}\n[Completed Note]: {notes}".strip()
    follow_up.save()

    AuditLog.objects.create(
        user=user,
        action="FOLLOWUP_COMPLETED",
        resource_type="crm.FollowUp",
        resource_id=str(follow_up.id),
        correlation_id=get_current_correlation_id(),
        changes={"status": FollowUpStatusChoices.COMPLETED},
    )

    return follow_up


@transaction.atomic
def cancel_follow_up(
    *,
    follow_up: FollowUp,
    user: User,
    reason: str,
) -> FollowUp:
    """Cancels a follow-up with mandatory reason."""
    follow_up.status = FollowUpStatusChoices.CANCELLED
    follow_up.cancellation_reason = reason.strip()
    follow_up.save()

    AuditLog.objects.create(
        user=user,
        action="FOLLOWUP_CANCELLED",
        resource_type="crm.FollowUp",
        resource_id=str(follow_up.id),
        correlation_id=get_current_correlation_id(),
        changes={"status": FollowUpStatusChoices.CANCELLED, "reason": reason},
    )

    return follow_up

