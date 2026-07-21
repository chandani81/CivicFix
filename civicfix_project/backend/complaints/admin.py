from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Complaint, ComplaintStatusHistory, ComplaintUpdate, Notification

User = get_user_model()


class ComplaintStatusHistoryInline(admin.TabularInline):
    model = ComplaintStatusHistory
    extra = 0
    readonly_fields = ["status", "changed_by", "note", "created_at"]


class ComplaintUpdateInline(admin.TabularInline):
    model = ComplaintUpdate
    extra = 0
    readonly_fields = ["posted_by", "message", "created_at"]


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "category", "department", "status", "is_emergency", "citizen", "created_at"]
    list_filter = ["status", "category", "is_emergency", "department"]
    search_fields = ["title", "description", "citizen__email"]
    inlines = [ComplaintStatusHistoryInline, ComplaintUpdateInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Citizen dropdown: only citizen accounts -- never admin or department staff.
        if db_field.name == "citizen":
            kwargs["queryset"] = User.objects.filter(role=User.Role.CITIZEN)
        # Department dropdown: Department objects only (this is already the case since
        # Complaint.department is a ForeignKey to Department, not User -- listed here
        # explicitly so the rule is easy to find).
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "kind", "message", "is_read", "created_at"]
    list_filter = ["kind", "is_read"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Recipient dropdown: citizens or department staff only -- never admin/superuser.
        if db_field.name == "recipient":
            kwargs["queryset"] = User.objects.filter(role__in=[User.Role.CITIZEN, User.Role.DEPARTMENT])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
