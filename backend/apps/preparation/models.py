"""Student Preparation, Assessments, Mock Interviews & Readiness Certification (MOD-006)."""
from decimal import Decimal
from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class ResumeReviewStatusChoices(models.TextChoices):
    APPROVED = "APPROVED", "Approved for Placement"
    NEEDS_IMPROVEMENT = "NEEDS_IMPROVEMENT", "Needs Improvement"


class AssessmentTypeChoices(models.TextChoices):
    APTITUDE = "APTITUDE", "Quantitative & Logical Aptitude"
    TECHNICAL = "TECHNICAL", "Core Technical Assessment"
    CODING = "CODING", "Hands-on Coding Assessment"


class MockStatusChoices(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    CONDUCTED = "CONDUCTED", "Conducted & Evaluated"
    CANCELLED = "CANCELLED", "Cancelled"


class ResumeReview(TimeStampedModel):
    """ATS and formatting review performed by placement trainers."""

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="resume_reviews",
    )
    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resume_reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_resume_reviews",
    )
    score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("0.0"),
        help_text="Resume evaluation score out of 10.0",
    )
    status = models.CharField(
        max_length=32,
        choices=ResumeReviewStatusChoices.choices,
        default=ResumeReviewStatusChoices.NEEDS_IMPROVEMENT,
        db_index=True,
    )
    notes = models.TextField(help_text="Specific improvement feedback for the candidate.")

    class Meta:
        db_table = "preparation_resume_review"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Resume Review: {self.student.roll_number} - {self.status} ({self.score}/10)"


class AssessmentRecord(TimeStampedModel):
    """Quantitative evaluation record across aptitude, technical, or coding assessments."""

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="assessment_records",
    )
    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessment_records",
    )
    test_type = models.CharField(
        max_length=32,
        choices=AssessmentTypeChoices.choices,
        default=AssessmentTypeChoices.TECHNICAL,
        db_index=True,
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("100.00"))
    pass_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("60.00"))
    is_passed = models.BooleanField(default=False, db_index=True)
    conducted_at = models.DateTimeField()

    class Meta:
        db_table = "preparation_assessment_record"
        ordering = ["-conducted_at"]

    def save(self, *args, **kwargs):
        self.is_passed = self.score >= self.pass_threshold
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        res = "PASS" if self.is_passed else "FAIL"
        return f"{self.student.roll_number} {self.test_type}: {self.score}/{self.max_score} ({res})"


class MockInterview(TimeStampedModel):
    """1-on-1 mock interview simulating placement drive interviews."""

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="mock_interviews",
    )
    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mock_interviews",
    )
    interviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_mocks",
    )
    scheduled_date = models.DateTimeField()
    conducted_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=MockStatusChoices.choices,
        default=MockStatusChoices.SCHEDULED,
        db_index=True,
    )
    technical_score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("0.0"),
        help_text="Technical knowledge score (max 25.0)",
    )
    communication_score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("0.0"),
        help_text="Communication & articulation score (max 15.0)",
    )
    problem_solving_score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("0.0"),
        help_text="Problem solving & critical thinking score (max 10.0)",
    )
    aggregate_score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal("0.0"),
        help_text="Aggregate score (max 50.0)",
    )
    feedback = models.TextField(blank=True)
    is_recommended = models.BooleanField(
        default=False,
        help_text="Whether candidate is recommended for corporate placement drives.",
    )

    class Meta:
        db_table = "preparation_mock_interview"
        ordering = ["-scheduled_date"]

    def save(self, *args, **kwargs):
        self.aggregate_score = (
            self.technical_score + self.communication_score + self.problem_solving_score
        )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        rec = "RECOMMENDED" if self.is_recommended else "NOT_RECOMMENDED"
        return f"Mock: {self.student.roll_number} - {self.aggregate_score}/50 ({rec})"


class ReadinessCertification(TimeStampedModel):
    """Step 23 Hard Gate: Certified clearance required before candidate submission to corporate HR."""

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="readiness_certifications",
    )
    job = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.CASCADE,
        related_name="readiness_certifications",
    )
    is_certified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Placement Readiness Certification sign-off.",
    )
    certified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_certifications",
    )
    certified_at = models.DateTimeField(auto_now_add=True)
    certification_notes = models.TextField(blank=True)

    class Meta:
        db_table = "preparation_readiness_certification"
        ordering = ["-certified_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "job"],
                name="unique_readiness_certification_per_job",
            )
        ]

    def __str__(self) -> str:
        status_str = "CERTIFIED" if self.is_certified else "UNCERTIFIED"
        return f"{self.student.roll_number} for {self.job.title}: {status_str}"
