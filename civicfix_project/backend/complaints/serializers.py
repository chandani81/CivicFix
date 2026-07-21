from rest_framework import serializers

from departments.models import Department
from departments.serializers import DepartmentSerializer

from .models import Complaint, ComplaintStatusHistory, ComplaintUpdate, Notification


class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(source="changed_by.email", read_only=True)

    class Meta:
        model = ComplaintStatusHistory
        fields = ["id", "status", "changed_by_email", "note", "created_at"]


class ComplaintUpdateSerializer(serializers.ModelSerializer):
    posted_by_email = serializers.CharField(source="posted_by.email", read_only=True)

    class Meta:
        model = ComplaintUpdate
        fields = ["id", "message", "posted_by_email", "created_at"]
        read_only_fields = ["posted_by_email"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "complaint", "kind", "message", "is_read", "created_at"]
        read_only_fields = fields


class ComplaintCreateSerializer(serializers.ModelSerializer):
    """
    Citizen-facing creation form, matching the notebook plan:
    title, description, category (dropdown incl. Road damage, Water leakage,
    Garbage, Street light, Drainage, Others), photo upload, location.
    Category may be left blank -> AI auto-categorizes from title/description.
    """

    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False, allow_null=True)
    category = serializers.ChoiceField(choices=Complaint.Category.choices, required=False)

    class Meta:
        model = Complaint
        fields = ["id", "title", "description", "category", "photo", "latitude", "longitude", "address"]
        read_only_fields = ["id"]


class ComplaintListSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    citizen_email = serializers.CharField(source="citizen.email", read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id", "title", "category", "category_display", "status", "status_display",
            "department", "department_name", "citizen_email", "is_emergency",
            "address", "photo", "created_at", "updated_at",
        ]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    department = DepartmentSerializer(read_only=True)
    citizen_email = serializers.CharField(source="citizen.email", read_only=True)
    status_history = ComplaintStatusHistorySerializer(many=True, read_only=True)
    updates = ComplaintUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            "id", "title", "description", "category", "category_display",
            "department", "photo", "latitude", "longitude", "address",
            "status", "status_display", "is_emergency", "emergency_confidence",
            "emergency_reason", "auto_categorized", "citizen_email",
            "status_history", "updates", "created_at", "updated_at", "resolved_at",
        ]


class StatusUpdateSerializer(serializers.Serializer):
    """Used by department/admin to move a complaint through pending -> in_progress -> resolved."""

    status = serializers.ChoiceField(choices=Complaint.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
