"""Placement Drives & Multi-Round Interview Management Models (MOD-008)."""
from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class DriveModeChoices(models.TextChoices):
    VIRTUAL = "VIRTUAL", "Virtual / Online Video"
    IN_PERSON = "IN_PERSON", "On-Campus / In-Person"
    HYBRID = "HYBRID", "Hybrid"


class DriveStatusChoices(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Drive Scheduled"
    IN_PROGRESS = "IN_PROGRESS", "Drive In Progress"
    COMPLETED = "COMPLETED", "Drive Completed"
    CANCELLED = "CANCELLED", "Drive Cancelled"


class RoundTypeChoices(models.TextChoices):
    APTITUDE = "APTITUDE", "Round: Online Aptitude / Screening"
    CODING = "CODING", "Round: Hands-on Coding Challenge"
    TECHNICAL = "TECHNICAL", "Round: Technical Interview"
    HR = "HR", "Round: HR & Culture Fit Interview"
    GROUP_DISCUSSION = "GROUP_DISCUSSION", "Round: Group Discussion"


class AttendanceChoices(models.TextChoices):
    PENDING = "PENDING", "Pending Confirmation"
    CONFIRMED = "CONFIRMED", "Confirmed by Candidate"
    PRESENT = "PRESENT", "Present & Attended"
    ABSENT = "ABSENT", "Absent / No-Show"
    RESCHEDULED = "RESCHEDULED", "Rescheduled"


class RoundOutcomeChoices(models.TextChoices):
    PENDING = "PENDING", "Evaluation Pending"
    SELECTED = "SELECTED", "Selected / Final Clear"
    NEXT_ROUND = "NEXT_ROUND", "Advanced to Next Round"
    ON_HOLD = "ON_HOLD", "On Hold / Waitlisted"
    NOT_SELECTED = "NOT_SELECTED", "Not Selected"


class PlacementDrive(TimeStampedModel):
    """Placement Drive event coordinating interviews for an approved job requirement."""

    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.CASCADE,
        related_name="placement_drives",
    )
    drive_code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Standardized drive identifier (e.g. DRV-2026-001).",
    )
    title = models.CharField(max_length=255)
    drive_date = models.DateTimeField(db_index=True)
    venue_or_link = models.CharField(max_length=512)
    drive_mode = models.CharField(
        max_length=32,
        choices=DriveModeChoices.choices,
        default=DriveModeChoices.VIRTUAL,
    )
    status = models.CharField(
        max_length=32,
        choices=DriveStatusChoices.choices,
        default=DriveStatusChoices.SCHEDULED,
        db_index=True,
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coordinated_drives",
    )
    instructions = models.TextField(blank=True)

    class Meta:
        db_table = "interviews_drive"
        ordering = ["-drive_date"]

    def __str__(self) -> str:
        return f"{self.drive_code}: {self.title} ({self.status})"


class InterviewRound(TimeStampedModel):
    """Specific evaluation stage within a PlacementDrive (e.g. Round 1 Coding, Round 2 Tech)."""

    drive = models.ForeignKey(
        PlacementDrive,
        on_delete=models.CASCADE,
        related_name="rounds",
    )
    round_number = models.PositiveSmallIntegerField(default=1)
    round_type = models.CharField(
        max_length=32,
        choices=RoundTypeChoices.choices,
        default=RoundTypeChoices.TECHNICAL,
    )
    round_name = models.CharField(max_length=128)
    instructions = models.TextField(blank=True)

    class Meta:
        db_table = "interviews_round"
        ordering = ["drive", "round_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["drive", "round_number"],
                name="unique_round_number_per_drive",
            )
        ]

    def __str__(self) -> str:
        return f"{self.drive.drive_code} - Round {self.round_number}: {self.round_name}"


class InterviewSlot(TimeStampedModel):
    """Individual candidate interview slot tracking schedule, attendance, and round outcome."""

    round = models.ForeignKey(
        InterviewRound,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="interview_slots",
    )
    scheduled_time = models.DateTimeField(db_index=True)
    meeting_url = models.CharField(max_length=512, blank=True)
    attendance_status = models.CharField(
        max_length=32,
        choices=AttendanceChoices.choices,
        default=AttendanceChoices.PENDING,
        db_index=True,
    )
    evaluator_notes = models.TextField(
        blank=True,
        help_text="CONFIDENTIAL: Internal evaluator assessment remarks; never exposed to student.",
    )
    outcome = models.CharField(
        max_length=32,
        choices=RoundOutcomeChoices.choices,
        default=RoundOutcomeChoices.PENDING,
        db_index=True,
    )
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluated_slots",
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "interviews_slot"
        ordering = ["scheduled_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["round", "student"],
                name="unique_candidate_slot_per_round",
            )
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} in {self.round} ({self.attendance_status} -> {self.outcome})"

