"""Recruitment CRM REST Views."""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.crm.models import Company, HRContact, FollowUp
from apps.crm.permissions import (
    IsCrmStaffOrReadOnly,
    CanManageCompany,
    CanManageFollowUp,
)
from apps.crm.selectors import (
    list_companies,
    get_company_by_id,
    list_hr_contacts,
    list_outreach_activities,
    list_follow_ups,
)
from apps.crm.services import (
    create_company,
    update_company,
    detect_company_duplicates,
    create_hr_contact,
    update_hr_contact,
    log_outreach_activity,
    create_follow_up,
    complete_follow_up,
    cancel_follow_up,
)
from apps.crm.serializers import (
    CompanyListSerializer,
    CompanyDetailSerializer,
    CompanyCreateSerializer,
    CompanyUpdateSerializer,
    DuplicateCheckInputSerializer,
    HRContactSerializer,
    HRContactCreateSerializer,
    OutreachActivitySerializer,
    OutreachActivityCreateSerializer,
    FollowUpSerializer,
    FollowUpCreateSerializer,
    FollowUpCompleteSerializer,
    FollowUpCancelSerializer,
)


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CompanyListCreateAPIView(APIView):
    """List hiring partner companies or create a new prospect company."""

    permission_classes = [IsCrmStaffOrReadOnly]
    pagination_class = StandardResultsPagination

    @extend_schema(
        summary="List Target Companies",
        parameters=[
            OpenApiParameter("search", str, description="Search term matching name, website or domain"),
            OpenApiParameter("status", str, description="Filter by company lifecycle status"),
            OpenApiParameter("industry", str, description="Filter by industry category"),
            OpenApiParameter("source", str, description="Filter by acquisition channel"),
            OpenApiParameter("tier", str, description="Filter by company tier"),
            OpenApiParameter("assigned_to", str, description="Filter by assigned executive UUID"),
        ],
        responses={200: CompanyListSerializer(many=True)},
    )
    def get(self, request):
        qs = list_companies(
            search=request.query_params.get("search"),
            status=request.query_params.get("status"),
            industry=request.query_params.get("industry"),
            source=request.query_params.get("source"),
            tier=request.query_params.get("tier"),
            assigned_to_id=request.query_params.get("assigned_to"),
        )
        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(qs, request)
        serializer = CompanyListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="Create Target Company",
        request=CompanyCreateSerializer,
        responses={201: CompanyDetailSerializer, 400: dict},
    )
    def post(self, request):
        serializer = CompanyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            company = create_company(
                name=serializer.validated_data["name"],
                website=serializer.validated_data.get("website", ""),
                industry=serializer.validated_data.get("industry", ""),
                source=serializer.validated_data.get("source", ""),
                status=serializer.validated_data.get("status", ""),
                tier=serializer.validated_data.get("tier", ""),
                assigned_to=serializer.validated_data.get("assigned_to"),
                notes=serializer.validated_data.get("notes", ""),
                user=request.user,
                allow_duplicate=serializer.validated_data.get("allow_duplicate", False),
            )
            # Re-fetch with prefetching
            company = get_company_by_id(str(company.id))
            return Response(CompanyDetailSerializer(company).data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class CompanyDetailAPIView(APIView):
    """Retrieve, update, or soft-delete a specific hiring partner company."""

    permission_classes = [IsCrmStaffOrReadOnly, CanManageCompany]

    @extend_schema(summary="Get Company Detail", responses={200: CompanyDetailSerializer, 404: dict})
    def get(self, request, company_id):
        company = get_company_by_id(str(company_id))
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, company)
        return Response(CompanyDetailSerializer(company).data)

    @extend_schema(summary="Update Company", request=CompanyUpdateSerializer, responses={200: CompanyDetailSerializer})
    def patch(self, request, company_id):
        company = get_company_by_id(str(company_id))
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, company)

        serializer = CompanyUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_company = update_company(
            company=company,
            user=request.user,
            **serializer.validated_data,
        )
        updated_company = get_company_by_id(str(updated_company.id))
        return Response(CompanyDetailSerializer(updated_company).data)

    @extend_schema(summary="Soft Delete Company", responses={204: None})
    def delete(self, request, company_id):
        company = get_company_by_id(str(company_id))
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, company)

        company.is_deleted = True
        company.save(update_fields=["is_deleted", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyCheckDuplicateAPIView(APIView):
    """Pre-flight endpoint analyzing company name and website against database for duplicates."""

    permission_classes = [IsCrmStaffOrReadOnly]

    @extend_schema(
        summary="Check Duplicate Company",
        request=DuplicateCheckInputSerializer,
        responses={200: dict},
    )
    def post(self, request):
        serializer = DuplicateCheckInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = detect_company_duplicates(
            name=serializer.validated_data["name"],
            website=serializer.validated_data.get("website", ""),
            exclude_company_id=serializer.validated_data.get("exclude_company_id"),
        )
        return Response(result)


class CompanyHRContactListCreateAPIView(APIView):
    """List or add HR recruiters and talent acquisition contacts for a specific company."""

    permission_classes = [IsCrmStaffOrReadOnly]

    @extend_schema(summary="List Company HR Contacts", responses={200: HRContactSerializer(many=True)})
    def get(self, request, company_id):
        company = get_company_by_id(str(company_id))
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        contacts = list_hr_contacts(company_id=str(company.id))
        return Response(HRContactSerializer(contacts, many=True).data)

    @extend_schema(summary="Create Company HR Contact", request=HRContactCreateSerializer, responses={201: HRContactSerializer})
    def post(self, request, company_id):
        company = get_company_by_id(str(company_id))
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = HRContactCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact = create_hr_contact(
            company=company,
            user=request.user,
            **serializer.validated_data,
        )
        return Response(HRContactSerializer(contact).data, status=status.HTTP_201_CREATED)


class HRContactDetailAPIView(APIView):
    """Retrieve, update or soft-delete a specific HR contact."""

    permission_classes = [IsCrmStaffOrReadOnly]

    @extend_schema(summary="Get HR Contact Detail", responses={200: HRContactSerializer})
    def get(self, request, contact_id):
        try:
            contact = HRContact.objects.select_related("company").get(id=contact_id, is_deleted=False)
        except HRContact.DoesNotExist:
            return Response({"detail": "HR Contact not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(HRContactSerializer(contact).data)

    @extend_schema(summary="Update HR Contact", request=HRContactCreateSerializer, responses={200: HRContactSerializer})
    def patch(self, request, contact_id):
        try:
            contact = HRContact.objects.select_related("company").get(id=contact_id, is_deleted=False)
        except HRContact.DoesNotExist:
            return Response({"detail": "HR Contact not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = HRContactCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_contact = update_hr_contact(
            contact=contact,
            user=request.user,
            **serializer.validated_data,
        )
        return Response(HRContactSerializer(updated_contact).data)

    @extend_schema(summary="Soft Delete HR Contact", responses={204: None})
    def delete(self, request, contact_id):
        try:
            contact = HRContact.objects.get(id=contact_id, is_deleted=False)
        except HRContact.DoesNotExist:
            return Response({"detail": "HR Contact not found."}, status=status.HTTP_404_NOT_FOUND)

        contact.is_deleted = True
        contact.save(update_fields=["is_deleted", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyOutreachListCreateAPIView(APIView):
    """List or log outreach touchpoints (calls, emails, LinkedIn InMails) for a company."""

    permission_classes = [IsCrmStaffOrReadOnly]

    @extend_schema(summary="List Company Outreach Activities", responses={200: OutreachActivitySerializer(many=True)})
    def get(self, request, company_id):
        company = get_company_by_id(str(company_id))
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
        activities = list_outreach_activities(company_id=str(company.id))
        return Response(OutreachActivitySerializer(activities, many=True).data)

    @extend_schema(
        summary="Log Outreach Activity Touchpoint",
        request=OutreachActivityCreateSerializer,
        responses={201: OutreachActivitySerializer},
    )
    def post(self, request, company_id):
        company = get_company_by_id(str(company_id))
        if not company:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OutreachActivityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contact = None
        contact_id = serializer.validated_data.get("contact_id")
        if contact_id:
            try:
                contact = HRContact.objects.get(id=contact_id, company=company, is_deleted=False)
            except HRContact.DoesNotExist:
                return Response({"detail": "Contact not found for this company."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            activity = log_outreach_activity(
                company=company,
                contact=contact,
                executive=request.user,
                channel=serializer.validated_data["channel"],
                outcome=serializer.validated_data["outcome"],
                notes=serializer.validated_data["notes"],
                next_action=serializer.validated_data.get("next_action", ""),
                follow_up_date=serializer.validated_data.get("follow_up_date"),
            )
            return Response(OutreachActivitySerializer(activity).data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class FollowUpListCreateAPIView(APIView):
    """List actionable follow-up tasks with state filters or schedule a new task."""

    permission_classes = [IsCrmStaffOrReadOnly]
    pagination_class = StandardResultsPagination

    @extend_schema(
        summary="List Actionable Follow-Up Tasks",
        parameters=[
            OpenApiParameter("filter_type", str, description="'due_today', 'overdue', or 'upcoming'"),
            OpenApiParameter("status", str, description="Task status (PENDING, COMPLETED, CANCELLED)"),
            OpenApiParameter("assigned_to", str, description="Assigned executive UUID"),
            OpenApiParameter("company", str, description="Target company UUID"),
        ],
        responses={200: FollowUpSerializer(many=True)},
    )
    def get(self, request):
        qs = list_follow_ups(
            assigned_to_id=request.query_params.get("assigned_to"),
            company_id=request.query_params.get("company"),
            status=request.query_params.get("status"),
            filter_type=request.query_params.get("filter_type"),
        )
        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(qs, request)
        serializer = FollowUpSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(summary="Schedule Follow-Up Task", request=FollowUpCreateSerializer, responses={201: FollowUpSerializer})
    def post(self, request):
        serializer = FollowUpCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        follow_up = create_follow_up(
            company=serializer.validated_data["company"],
            contact=serializer.validated_data.get("contact"),
            assigned_to=serializer.validated_data["assigned_to"],
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get("description", ""),
            due_date=serializer.validated_data["due_date"],
            priority=serializer.validated_data.get("priority", ""),
            user=request.user,
        )
        return Response(FollowUpSerializer(follow_up).data, status=status.HTTP_201_CREATED)


class FollowUpDetailAPIView(APIView):
    """Retrieve a specific follow-up task."""

    permission_classes = [IsCrmStaffOrReadOnly, CanManageFollowUp]

    @extend_schema(summary="Get Follow-Up Detail", responses={200: FollowUpSerializer})
    def get(self, request, follow_up_id):
        try:
            follow_up = FollowUp.objects.select_related("company", "contact", "assigned_to", "completed_by").get(
                id=follow_up_id, is_deleted=False
            )
        except FollowUp.DoesNotExist:
            return Response({"detail": "Follow-Up task not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, follow_up)
        return Response(FollowUpSerializer(follow_up).data)


class FollowUpCompleteAPIView(APIView):
    """Mark an active follow-up task as completed."""

    permission_classes = [IsCrmStaffOrReadOnly, CanManageFollowUp]

    @extend_schema(summary="Complete Follow-Up Task", request=FollowUpCompleteSerializer, responses={200: FollowUpSerializer})
    def post(self, request, follow_up_id):
        try:
            follow_up = FollowUp.objects.select_related("company", "assigned_to").get(
                id=follow_up_id, is_deleted=False
            )
        except FollowUp.DoesNotExist:
            return Response({"detail": "Follow-Up task not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, follow_up)

        serializer = FollowUpCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        completed = complete_follow_up(
            follow_up=follow_up,
            user=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response(FollowUpSerializer(completed).data)


class FollowUpCancelAPIView(APIView):
    """Cancel an active follow-up task with mandatory reason."""

    permission_classes = [IsCrmStaffOrReadOnly, CanManageFollowUp]

    @extend_schema(summary="Cancel Follow-Up Task", request=FollowUpCancelSerializer, responses={200: FollowUpSerializer})
    def post(self, request, follow_up_id):
        try:
            follow_up = FollowUp.objects.select_related("company", "assigned_to").get(
                id=follow_up_id, is_deleted=False
            )
        except FollowUp.DoesNotExist:
            return Response({"detail": "Follow-Up task not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, follow_up)

        serializer = FollowUpCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cancelled = cancel_follow_up(
            follow_up=follow_up,
            user=request.user,
            reason=serializer.validated_data["reason"],
        )
        return Response(FollowUpSerializer(cancelled).data)
