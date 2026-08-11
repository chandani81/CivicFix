from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCitizen
from ai_services.categorization import categorize, suggest_department
from ai_services.image_detection import detect_emergency
from ai_services.location_service import reverse_geocode
from departments.models import Department

from .models import Complaint, ComplaintStatusHistory, ComplaintUpdate, Notification
from .permissions import CanUpdateStatus, IsComplaintParticipant
from .serializers import (
    ComplaintCreateSerializer,
    ComplaintDetailSerializer,
    ComplaintListSerializer,
    ComplaintUpdateSerializer,
    NotificationSerializer,
    StatusUpdateSerializer,
)


def _notify(recipient, kind, message, complaint=None):
    if recipient is None:
        return
    Notification.objects.create(recipient=recipient, kind=kind, message=message, complaint=complaint)


class ComplaintListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/complaints/   -> role-scoped list
         citizen    -> only their own complaints
         department -> only complaints routed to their department
         admin      -> all complaints
         Supports ?status=&category=&is_emergency=
    POST /api/complaints/   -> citizen only. Runs AI categorization,
                                emergency image detection, and reverse
                                geocoding, then routes to a department.
    """

    filterset_fields = ["status", "category", "is_emergency", "department"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ComplaintCreateSerializer
        return ComplaintListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsCitizen()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Complaint.objects.select_related("department", "citizen")

        if user.is_citizen:
            qs = qs.filter(citizen=user)
        elif user.is_department_staff:
            qs = qs.filter(department=user.department)
        # admin sees everything

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        title = serializer.validated_data.get("title", "")
        description = serializer.validated_data.get("description", "")
        category = serializer.validated_data.get("category")
        auto_categorized = False

        if not category:
            category = categorize(title, description)
            auto_categorized = True

        department = Department.objects.filter(category=category, is_active=True).first()

        lat = serializer.validated_data.get("latitude")
        lng = serializer.validated_data.get("longitude")
        address = serializer.validated_data.get("address") or ""
        if lat is not None and lng is not None and not address:
            address = reverse_geocode(float(lat), float(lng))

        # Save first so the photo (if any) is written to disk and has a real
        # file path -- an in-memory upload doesn't have one, so emergency
        # image analysis needs to run *after* the file is persisted.
        complaint = serializer.save(
            citizen=user,
            category=category,
            department=department,
            auto_categorized=auto_categorized,
            address=address,
        )

        image_path = None
        if complaint.photo and hasattr(complaint.photo, "path"):
            try:
                image_path = complaint.photo.path
            except (ValueError, NotImplementedError):
                image_path = None

        emergency_result = detect_emergency(image_path=image_path, title=title, description=description)
        complaint.is_emergency = emergency_result.is_emergency
        complaint.emergency_confidence = emergency_result.confidence
        complaint.emergency_reason = emergency_result.reason
        complaint.save(update_fields=["is_emergency", "emergency_confidence", "emergency_reason"])

        ComplaintStatusHistory.objects.create(
            complaint=complaint, status=Complaint.Status.PENDING, changed_by=user, note="Complaint submitted."
        )

        if department:
            for staff in department.staff_members.filter(is_active=True):
                _notify(
                    staff, Notification.Kind.STATUS_CHANGE,
                    f"New complaint submitted: {complaint.title}", complaint,
                )

        if emergency_result.is_emergency:
            for admin_user in _admin_users():
                _notify(
                    admin_user, Notification.Kind.EMERGENCY,
                    f"AI flagged an EMERGENCY complaint: {complaint.title}", complaint,
                )


def _admin_users():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(role=User.Role.ADMIN) | User.objects.filter(is_superuser=True)


class ComplaintDetailView(generics.RetrieveAPIView):
    """GET /api/complaints/<id>/ - full detail incl. status history + updates thread."""

    queryset = Complaint.objects.select_related("department", "citizen").prefetch_related(
        "status_history", "updates"
    )
    serializer_class = ComplaintDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsComplaintParticipant]


class ComplaintStatusUpdateView(APIView):
    """
    PATCH /api/complaints/<id>/status/  {status, note}
    Department staff (of the assigned dept) or admin only.
    Tracks the change in status_history, notifies the citizen, and warns
    admin if a complaint has sat un-resolved without department action.
    """

    permission_classes = [permissions.IsAuthenticated, CanUpdateStatus]

    def patch(self, request, pk):
        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, complaint)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        note = serializer.validated_data.get("note", "")

        complaint.status = new_status
        if new_status == Complaint.Status.RESOLVED:
            complaint.resolved_at = timezone.now()
        complaint.save(update_fields=["status", "resolved_at", "updated_at"])

        ComplaintStatusHistory.objects.create(
            complaint=complaint, status=new_status, changed_by=request.user, note=note
        )

        _notify(
            complaint.citizen, Notification.Kind.STATUS_CHANGE,
            f"Your complaint '{complaint.title}' is now {complaint.get_status_display()}.",
            complaint,
        )

        return Response(ComplaintDetailSerializer(complaint).data)


class ComplaintUpdateListCreateView(generics.ListCreateAPIView):
    """
    GET/POST /api/complaints/<id>/updates/
    Department/admin post progress updates; citizen (owner) can read them.
    Matches the notebook's "Receives updates" page.
    """

    serializer_class = ComplaintUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsComplaintParticipant]

    def get_complaint(self):
        complaint = get_object_or_404(Complaint, pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, complaint)
        return complaint

    def get_queryset(self):
        complaint = self.get_complaint()
        return ComplaintUpdate.objects.filter(complaint=complaint)

    def perform_create(self, serializer):
        complaint = self.get_complaint()
        user = self.request.user
        if not (user.is_admin_role or user.is_department_staff):
            raise PermissionDenied("Only department staff or admin can post updates.")

        update = serializer.save(complaint=complaint, posted_by=user)
        _notify(
            complaint.citizen, Notification.Kind.NEW_UPDATE,
            f"New update on '{complaint.title}': {update.message[:100]}", complaint,
        )


class NotificationListView(generics.ListAPIView):
    """GET /api/complaints/notifications/ - current user's notifications, newest first."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationMarkReadView(APIView):
    """POST /api/complaints/notifications/<id>/read/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, recipient=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return Response({"message": "Marked as read."})


class DashboardStatsView(APIView):
    """
    GET /api/complaints/stats/
    Role-scoped counts for a dashboard: total / pending / in_progress /
    resolved / emergency, matching the "Track status" requirement.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Complaint.objects.all()
        if user.is_citizen:
            qs = qs.filter(citizen=user)
        elif user.is_department_staff:
            qs = qs.filter(department=user.department)

        data = {
            "total": qs.count(),
            "pending": qs.filter(status=Complaint.Status.PENDING).count(),
            "in_progress": qs.filter(status=Complaint.Status.IN_PROGRESS).count(),
            "resolved": qs.filter(status=Complaint.Status.RESOLVED).count(),
            "emergency": qs.filter(is_emergency=True).count(),
        }
        return Response(data)
