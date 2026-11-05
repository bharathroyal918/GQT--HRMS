"""Selectors for Student Management (MOD-005)."""
from typing import Optional
from decimal import Decimal
from django.db.models import QuerySet, Count, Q
from apps.students.models import StudentProfile, DriveRegistration, CandidateCohort


def list_students(
    *,
    search: Optional[str] = None,
    branch: Optional[str] = None,
    graduation_year: Optional[int] = None,
    placement_status: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> QuerySet[StudentProfile]:
    """Retrieve filtered student profiles."""
    qs = StudentProfile.objects.prefetch_related("resumes").order_by("roll_number")

    if search:
        search = search.strip()
        qs = qs.filter(
            Q(roll_number__icontains=search)
            | Q(full_name__icontains=search)
            | Q(email__icontains=search)
            | Q(branch__icontains=search)
        )

    if branch:
        qs = qs.filter(branch__iexact=branch.strip())

    if graduation_year:
        qs = qs.filter(graduation_year=graduation_year)

    if placement_status:
        qs = qs.filter(placement_status=placement_status)

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    return qs


def get_student_metrics() -> dict:
    """Compute aggregate student placement statistics."""
    total = StudentProfile.objects.filter(is_active=True).count()
    placed = StudentProfile.objects.filter(placement_status="PLACED", is_active=True).count()
    seeking = StudentProfile.objects.filter(placement_status="SEEKING", is_active=True).count()
    opted_out = StudentProfile.objects.filter(placement_status="OPTED_OUT", is_active=True).count()

    placement_rate = (placed / total * 100) if total > 0 else 0.0

    branch_breakdown = list(
        StudentProfile.objects.filter(is_active=True)
        .values("branch")
        .annotate(total=Count("id"), placed=Count("id", filter=Q(placement_status="PLACED")))
        .order_by("-total")
    )

    return {
        "total_students": total,
        "placed_students": placed,
        "seeking_students": seeking,
        "opted_out_students": opted_out,
        "placement_rate_pct": round(placement_rate, 1),
        "branch_breakdown": branch_breakdown,
    }

