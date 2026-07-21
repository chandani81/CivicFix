from rest_framework import serializers

from .models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    staff_count = serializers.IntegerField(source="staff_members.count", read_only=True)

    class Meta:
        model = Department
        fields = [
            "id", "name", "category", "category_display", "description",
            "contact_email", "contact_phone", "is_active", "staff_count", "created_at",
        ]
