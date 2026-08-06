from django.core.validators import MaxValueValidator, MinValueValidator
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
    Garbage, Electricity, Drainage, Others), photo upload, location.
    Category may be left blank -> AI auto-categorizes from title/description.
    """

    # Leaflet returns more precision than the original API accepted.  Keep
    # these fields aligned with the model and validate real coordinate ranges.
    latitude = serializers.DecimalField(
        max_digits=12,
        decimal_places=8,
        required=False,
        allow_null=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = serializers.DecimalField(
        max_digits=12,
        decimal_places=8,
        required=False,
        allow_null=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    category = serializers.ChoiceField(choices=Complaint.Category.choices, required=False)

    class Meta:
        model = Complaint
        fields = ["id", "title", "description", "category", "photo", "latitude", "longitude", "address"]
        read_only_fields = ["id"]

    def validate_photo(self, value):
        max_size = 10 * 1024 * 1024
        if value and value.size > max_size:
            raise serializers.ValidationError("Photo must be 10 MB or smaller.")
        return value


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
    department_email_status = serializers.SerializerMethodField()

    def get_department_email_status(self, obj):
        if obj.department_email_sent_at:
            return "sent"
        if obj.department_email_error:
            return "failed"
        return "pending"

    class Meta:
        model = Complaint
        fields = [
            "id", "title", "description", "category", "category_display",
            "department", "photo", "latitude", "longitude", "address",
            "status", "status_display", "is_emergency", "emergency_confidence",
            "emergency_reason", "auto_categorized", "citizen_email",
            "department_email_status", "department_email_recipient",
            "department_email_sent_at",
            "status_history", "updates", "created_at", "updated_at", "resolved_at",
        ]


class StatusUpdateSerializer(serializers.Serializer):
    """Used by department/admin to move a complaint through pending -> in_progress -> resolved."""

    status = serializers.ChoiceField(choices=Complaint.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
