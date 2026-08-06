from django.conf import settings
from django.db import models

from departments.models import Department


def complaint_photo_path(instance, filename):
    return f"complaints/{instance.citizen_id}/{filename}"


class Complaint(models.Model):
    class Category(models.TextChoices):
        ROAD_DAMAGE = "road_damage", "Road Damage"
        WATER_LEAKAGE = "water_leakage", "Water Leakage"
        GARBAGE = "garbage", "Garbage"
        # Keep the stored key so existing records and integrations remain valid.
        STREET_LIGHT = "street_light", "Electricity"
        DRAINAGE = "drainage", "Drainage"
        OTHERS = "others", "Others"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    citizen = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="complaints"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=Category.choices)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints"
    )
    photo = models.ImageField(upload_to=complaint_photo_path, blank=True, null=True)

    # Location (OpenStreetMap integration)
    latitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # AI fields
    is_emergency = models.BooleanField(default=False)
    emergency_confidence = models.FloatField(default=0.0)
    emergency_reason = models.CharField(max_length=255, blank=True)
    auto_categorized = models.BooleanField(default=False)

    # Audit fields for the email produced after AI/category routing. Email
    # delivery is deliberately separate from complaint persistence so an SMTP
    # outage never causes a citizen's report to be lost.
    department_email_recipient = models.EmailField(blank=True)
    department_email_sent_at = models.DateTimeField(blank=True, null=True)
    department_email_error = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-is_emergency", "-created_at"]

    def __str__(self):
        return f"#{self.id} {self.title} ({self.status})"


class ComplaintStatusHistory(models.Model):
    """Audit trail: every status change on a complaint, per the 'Track status' requirement."""

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20, choices=Complaint.Status.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "Complaint status histories"

    def __str__(self):
        return f"{self.complaint_id} -> {self.status}"


class ComplaintUpdate(models.Model):
    """
    "Receives updates" from the citizen's notebook plan: a department/admin
    posts a progress update on a complaint, which the citizen can open and read.
    """

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="updates")
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Update on #{self.complaint_id} by {self.posted_by}"


class Notification(models.Model):
    """
    In-app notification queue, sent by Admin:
    - to Citizens about their complaint status
    - to Department Staff to remind them to work on a complaint
    - automatic SLA warnings / emergency flags for admins to act on
    """

    class Kind(models.TextChoices):
        STATUS_CHANGE = "status_change", "Status Change"
        NEW_UPDATE = "new_update", "New Update"
        SLA_WARNING = "sla_warning", "Department Inactivity Warning"
        EMERGENCY = "emergency", "Emergency Complaint"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    kind = models.CharField(max_length=30, choices=Kind.choices)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.kind}] to {self.recipient}: {self.message[:40]}"
