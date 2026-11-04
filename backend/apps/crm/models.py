"""Recruitment CRM Models: Company, HRContact, OutreachActivity, and FollowUp.

Engineered with five-layer architectural discipline, UUIDv4 primary keys,
normalized name indexing, duplicate checking support, and immutable audit compatibility.
"""
import re
from urllib.parse import urlparse
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


def extract_canonical_domain(website: str) -> str:
    """Extracts a normalized, canonical domain (e.g. 'infosys.com') from a website URL."""
    if not website:
        return ""
    url = website.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        # Remove any port if present
        domain = domain.split(":")[0]
        return domain.strip()
    except Exception:
        return ""


def normalize_company_name(name: str) -> str:
    """Normalizes company name: lowercases, strips corporate suffixes & special characters.

    E.g. 'Infosys Technologies Pvt. Ltd.' -> 'infosys technologies'
    """
    if not name:
        return ""
    cleaned = name.lower().strip()
    # Remove common Indian/Global corporate suffixes
    suffixes = [
        r"\bpvt\.?\s*ltd\.?\b",
        r"\bprivate\s+limited\b",
        r"\bltd\.?\b",
        r"\blimited\b",
        r"\binc\.?\b",
        r"\bincorporated\b",
        r"\bcorp\.?\b",
        r"\bcorporation\b",
        r"\bllc\b",
        r"\bllp\b",
    ]
    for suf in suffixes:
        cleaned = re.sub(suf, "", cleaned, flags=re.IGNORECASE)
    # Remove punctuation characters
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class IndustryChoices(models.TextChoices):
    IT_SERVICES = "IT_SERVICES", "IT Services & Consulting"
    PRODUCT_TECH = "PRODUCT_TECH", "Product / Software Tech"
    FINTECH = "FINTECH", "FinTech & Banking"
    EDTECH = "EDTECH", "EdTech & Learning"
    HEALTHCARE = "HEALTHCARE", "Healthcare & Pharma"
    MANUFACTURING = "MANUFACTURING", "Manufacturing & Core Engineering"
    ECOMMERCE = "ECOMMERCE", "E-Commerce & Retail"
    CONSULTING = "CONSULTING", "Management Consulting"
    TELECOM = "TELECOM", "Telecommunications"
    OTHER = "OTHER", "Other Industry"


class AcquisitionSourceChoices(models.TextChoices):
    OUTBOUND_CALLING = "OUTBOUND_CALLING", "Outbound Cold Calling"
    INBOUND_INQUIRY = "INBOUND_INQUIRY", "Inbound Inquiry"
    JOB_PORTAL = "JOB_PORTAL", "Job Portal Scraping / Lead"
    CAMPUS_ALUMNI = "CAMPUS_ALUMNI", "Alumni Referral / Network"
    LINKEDIN = "LINKEDIN", "LinkedIn Outreach"
    EXECUTIVE_REFERRAL = "EXECUTIVE_REFERRAL", "Executive / Leadership Referral"
    OTHER = "OTHER", "Other Source"


class CompanyStatusChoices(models.TextChoices):
    LEAD = "LEAD", "Lead / Prospect"
    CONTACTED = "CONTACTED", "Contacted / Outreach Initiated"
    ENGAGED = "ENGAGED", "Engaged / In Discussion"
    ACTIVE_HIRING_PARTNER = "ACTIVE_HIRING_PARTNER", "Active Hiring Partner"
    DORMANT = "DORMANT", "Dormant / No Immediate Requirement"
    BLACKLISTED = "BLACKLISTED", "Blacklisted / Do Not Contact"


class CompanyTierChoices(models.TextChoices):
    TIER_1 = "TIER_1", "Tier 1 (Enterprise / MNC)"
    TIER_2 = "TIER_2", "Tier 2 (Mid-Market / High Growth)"
    TIER_3 = "TIER_3", "Tier 3 (Startup / Boutique)"
    UNRATED = "UNRATED", "Unrated"


class PreferredChannelChoices(models.TextChoices):
    EMAIL = "EMAIL", "Corporate Email"
    PHONE = "PHONE", "Direct Phone Call"
    WHATSAPP = "WHATSAPP", "WhatsApp Messaging"
    LINKEDIN = "LINKEDIN", "LinkedIn InMail"


class ContactStatusChoices(models.TextChoices):
    ACTIVE = "ACTIVE", "Active Recruiter"
    INACTIVE = "INACTIVE", "Inactive"
    FORMER_EMPLOYEE = "FORMER_EMPLOYEE", "Left Organization"


class OutreachChannelChoices(models.TextChoices):
    PHONE = "PHONE", "Phone Call"
    EMAIL = "EMAIL", "Email Outreach"
    WHATSAPP = "WHATSAPP", "WhatsApp Message"
    LINKEDIN = "LINKEDIN", "LinkedIn Outreach"
    IN_PERSON = "IN_PERSON", "In-Person Meeting"
    OTHER = "OTHER", "Other Channel"


class OutreachOutcomeChoices(models.TextChoices):
    INTERESTED = "INTERESTED", "Interested in Hiring"
    FOLLOW_UP_REQUESTED = "FOLLOW_UP_REQUESTED", "Requested Callback / Follow-Up"
    NOT_INTERESTED = "NOT_INTERESTED", "Not Hiring / No Budget"
    CALL_NOT_ANSWERED = "CALL_NOT_ANSWERED", "Ringing / No Answer"
    WRONG_NUMBER = "WRONG_NUMBER", "Invalid / Wrong Number"
    GATEKEEPER_BLOCKED = "GATEKEEPER_BLOCKED", "Gatekeeper Refused Transfer"
    MEETING_SCHEDULED = "MEETING_SCHEDULED", "Virtual / In-Person Meeting Scheduled"
    REQUIREMENT_SHARED = "REQUIREMENT_SHARED", "Job Description Received"


class FollowUpPriorityChoices(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent / Escalated"


class FollowUpStatusChoices(models.TextChoices):
    PENDING = "PENDING", "Pending Action"
    COMPLETED = "COMPLETED", "Completed"
    RESCHEDULED = "RESCHEDULED", "Rescheduled"
    CANCELLED = "CANCELLED", "Cancelled"


class Company(TimeStampedModel):
    """Corporate Entity / Hiring Partner in the recruitment CRM pipeline."""

    name = models.CharField(max_length=255, db_index=True)
    normalized_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Automated lowercase canonical string for duplicate detection.",
    )
    website = models.URLField(max_length=500, blank=True, default="")
    canonical_domain = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Normalized root domain extracted from website for duplicate matching.",
    )
    industry = models.CharField(
        max_length=64,
        choices=IndustryChoices.choices,
        default=IndustryChoices.IT_SERVICES,
        db_index=True,
    )
    source = models.CharField(
        max_length=64,
        choices=AcquisitionSourceChoices.choices,
        default=AcquisitionSourceChoices.OUTBOUND_CALLING,
        db_index=True,
    )
    status = models.CharField(
        max_length=64,
        choices=CompanyStatusChoices.choices,
        default=CompanyStatusChoices.LEAD,
        db_index=True,
    )
    tier = models.CharField(
        max_length=32,
        choices=CompanyTierChoices.choices,
        default=CompanyTierChoices.UNRATED,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_companies",
        help_text="Acquisition / Calling executive responsible for this account.",
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_companies",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_companies",
    )

    class Meta:
        db_table = "crm_company"
        ordering = ["-created_at"]
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        indexes = [
            models.Index(fields=["status", "assigned_to"]),
            models.Index(fields=["canonical_domain"]),
            models.Index(fields=["normalized_name"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Automatically normalize name and canonical domain on save
        self.normalized_name = normalize_company_name(self.name)
        if self.website:
            self.canonical_domain = extract_canonical_domain(self.website)
        super().save(*args, **kwargs)


class HRContact(TimeStampedModel):
    """Recruiter, Talent Acquisition Lead, or HR Professional at a hiring partner."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="contacts",
        help_text="Corporate entity employing this contact.",
    )
    name = models.CharField(max_length=255, db_index=True)
    designation = models.CharField(max_length=128, blank=True, default="")
    department = models.CharField(max_length=128, blank=True, default="")
    email = models.EmailField(max_length=255, blank=True, default="", db_index=True)
    phone = models.CharField(max_length=32, blank=True, default="", db_index=True)
    alternate_phone = models.CharField(max_length=32, blank=True, default="")
    linkedin_url = models.URLField(max_length=500, blank=True, default="")
    preferred_channel = models.CharField(
        max_length=32,
        choices=PreferredChannelChoices.choices,
        default=PreferredChannelChoices.EMAIL,
    )
    status = models.CharField(
        max_length=32,
        choices=ContactStatusChoices.choices,
        default=ContactStatusChoices.ACTIVE,
        db_index=True,
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Designates this recruiter as the primary placement point of contact.",
    )
    notes = models.TextField(blank=True, default="")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_contacts",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_contacts",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_contacts",
    )

    class Meta:
        db_table = "crm_hr_contact"
        ordering = ["-is_primary", "-created_at"]
        verbose_name = "HR Contact"
        verbose_name_plural = "HR Contacts"
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.company.name})"

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.phone:
            self.phone = re.sub(r"[^\d+]", "", self.phone.strip())
        super().save(*args, **kwargs)


class OutreachActivity(TimeStampedModel):
    """Touchpoint log recording cold calls, emails, LinkedIn InMails, and meetings."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="outreach_activities",
    )
    contact = models.ForeignKey(
        HRContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outreach_activities",
    )
    executive = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="outreach_activities",
    )
    attempted_at = models.DateTimeField(default=timezone.now, db_index=True)
    channel = models.CharField(
        max_length=32,
        choices=OutreachChannelChoices.choices,
        default=OutreachChannelChoices.PHONE,
    )
    outcome = models.CharField(
        max_length=64,
        choices=OutreachOutcomeChoices.choices,
        default=OutreachOutcomeChoices.INTERESTED,
    )
    notes = models.TextField(help_text="Detailed notes summarizing the interaction.")
    next_action = models.CharField(max_length=255, blank=True, default="")
    follow_up_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "crm_outreach_activity"
        ordering = ["-attempted_at"]
        verbose_name = "Outreach Activity"
        verbose_name_plural = "Outreach Activities"
        indexes = [
            models.Index(fields=["company", "-attempted_at"]),
            models.Index(fields=["executive", "-attempted_at"]),
            models.Index(fields=["outcome"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel} to {self.company.name} by {self.executive.email} at {self.attempted_at.isoformat()}"


class FollowUp(TimeStampedModel):
    """Actionable follow-up scheduled for an executive regarding a corporate prospect."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="follow_ups",
    )
    contact = models.ForeignKey(
        HRContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="follow_ups",
        help_text="Follow-up remains active even if contact changes status.",
    )
    outreach_activity = models.ForeignKey(
        OutreachActivity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_follow_ups",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_follow_ups",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    due_date = models.DateTimeField(db_index=True)
    priority = models.CharField(
        max_length=32,
        choices=FollowUpPriorityChoices.choices,
        default=FollowUpPriorityChoices.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=FollowUpStatusChoices.choices,
        default=FollowUpStatusChoices.PENDING,
        db_index=True,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_follow_ups",
    )
    cancellation_reason = models.TextField(blank=True, default="")

    class Meta:
        db_table = "crm_follow_up"
        ordering = ["due_date", "-priority"]
        verbose_name = "Follow-Up"
        verbose_name_plural = "Follow-Ups"
        indexes = [
            models.Index(fields=["assigned_to", "status", "due_date"]),
            models.Index(fields=["company", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.company.name}) due {self.due_date.isoformat()}"

    @property
    def is_overdue(self) -> bool:
        """Determines if the follow-up is pending and past its due date."""
        if self.status in [FollowUpStatusChoices.COMPLETED, FollowUpStatusChoices.CANCELLED]:
            return False
        return self.due_date < timezone.now()

    @property
    def is_due_today(self) -> bool:
        """Determines if the follow-up is pending and due today in local time."""
        if self.status in [FollowUpStatusChoices.COMPLETED, FollowUpStatusChoices.CANCELLED]:
            return False
        today = timezone.localdate()
        return timezone.localtime(self.due_date).date() == today
