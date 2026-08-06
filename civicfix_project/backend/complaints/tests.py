from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ai_services.image_detection import EmergencyResult
from departments.models import Department

from .models import Complaint, ComplaintStatusHistory, Notification


User = get_user_model()


class ComplaintApiTests(APITestCase):
    def setUp(self):
        self.roads = Department.objects.create(
            name="Roads", category=Department.Category.ROAD_DAMAGE
        )
        self.water = Department.objects.create(
            name="Water", category=Department.Category.WATER_LEAKAGE
        )
        self.citizen = User.objects.create_user(
            email="citizen@example.com", password="StrongPassword!2026"
        )
        self.other_citizen = User.objects.create_user(
            email="other@example.com", password="StrongPassword!2026"
        )
        self.road_staff = User.objects.create_user(
            email="roads@example.com",
            password="StrongPassword!2026",
            role=User.Role.DEPARTMENT,
            department=self.roads,
        )
        self.water_staff = User.objects.create_user(
            email="water@example.com",
            password="StrongPassword!2026",
            role=User.Role.DEPARTMENT,
            department=self.water,
        )

    def make_complaint(self):
        complaint = Complaint.objects.create(
            citizen=self.citizen,
            title="Road pothole",
            description="A deep pothole",
            category=Complaint.Category.ROAD_DAMAGE,
            department=self.roads,
        )
        ComplaintStatusHistory.objects.create(
            complaint=complaint,
            status=Complaint.Status.PENDING,
            changed_by=self.citizen,
        )
        return complaint

    @patch("complaints.views.reverse_geocode", return_value="Kathmandu, Nepal")
    @patch(
        "complaints.views.detect_emergency",
        return_value=EmergencyResult(False, 0.0, "no emergency signals detected"),
    )
    def test_submission_accepts_leaflet_coordinate_precision(self, _detect, _geocode):
        self.client.force_authenticate(self.citizen)
        response = self.client.post(
            "/api/complaints/",
            {
                "title": "Large pothole",
                "description": "Broken road near the market",
                "latitude": "27.71724567",
                "longitude": "85.32401234",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        complaint = Complaint.objects.get(pk=response.data["id"])
        self.assertEqual(complaint.latitude, Decimal("27.71724567"))
        self.assertEqual(complaint.longitude, Decimal("85.32401234"))
        self.assertEqual(complaint.department, self.roads)
        self.assertTrue(complaint.auto_categorized)
        self.assertEqual(complaint.address, "Kathmandu, Nepal")
        self.assertTrue(
            Notification.objects.filter(recipient=self.road_staff, complaint=complaint).exists()
        )

    def test_submission_rejects_coordinates_outside_world_bounds(self):
        self.client.force_authenticate(self.citizen)
        response = self.client.post(
            "/api/complaints/",
            {
                "title": "Issue",
                "description": "Description",
                "latitude": "91.00000000",
                "longitude": "181.00000000",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("latitude", response.data)
        self.assertIn("longitude", response.data)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SEND_DEPARTMENT_EMAILS=True,
        FRONTEND_BASE_URL="https://civicfix.example",
    )
    @patch("complaints.views.categorize", return_value=Complaint.Category.ROAD_DAMAGE)
    @patch(
        "complaints.views.detect_emergency",
        return_value=EmergencyResult(True, 0.6, "urgent language detected"),
    )
    def test_ai_routed_complaint_is_emailed_to_department(self, _detect, _categorize):
        self.roads.contact_email = "roads@example.gov.np"
        self.roads.save(update_fields=["contact_email"])
        self.client.force_authenticate(self.citizen)
        response = self.client.post(
            "/api/complaints/",
            {
                "title": "Fire near a damaged pole",
                "description": "There is fire at the roadside electrical pole.",
                "address": "Ward 5, Kathmandu",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        complaint = Complaint.objects.get(pk=response.data["id"])
        self.assertTrue(complaint.auto_categorized)
        self.assertEqual(complaint.department, self.roads)
        self.assertEqual(complaint.department_email_recipient, "roads@example.gov.np")
        self.assertIsNotNone(complaint.department_email_sent_at)
        self.assertEqual(complaint.department_email_error, "")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["roads@example.gov.np"])
        self.assertIn("EMERGENCY", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].subject, mail.outbox[0].subject.upper())
        self.assertIn("Ward 5, Kathmandu", mail.outbox[0].body)
        self.assertIn("https://civicfix.example/department/complaint.html", mail.outbox[0].body)

    @override_settings(SEND_DEPARTMENT_EMAILS=True)
    @patch("complaints.email_routing.EmailMessage.send", side_effect=OSError("SMTP unavailable"))
    @patch("complaints.views.categorize", return_value=Complaint.Category.ROAD_DAMAGE)
    @patch(
        "complaints.views.detect_emergency",
        return_value=EmergencyResult(False, 0.0, "no emergency signals"),
    )
    def test_email_failure_never_loses_complaint(self, _detect, _categorize, _send):
        self.roads.contact_email = "roads@example.gov.np"
        self.roads.save(update_fields=["contact_email"])
        self.client.force_authenticate(self.citizen)
        response = self.client.post(
            "/api/complaints/",
            {"title": "Pothole", "description": "Deep road damage"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        complaint = Complaint.objects.get(pk=response.data["id"])
        self.assertIsNone(complaint.department_email_sent_at)
        self.assertIn("SMTP unavailable", complaint.department_email_error)

    @override_settings(SEND_DEPARTMENT_EMAILS=True)
    @patch("complaints.views.categorize", return_value=Complaint.Category.ROAD_DAMAGE)
    @patch(
        "complaints.views.detect_emergency",
        return_value=EmergencyResult(False, 0.0, "no emergency signals"),
    )
    def test_missing_department_email_is_recorded(self, _detect, _categorize):
        self.client.force_authenticate(self.citizen)
        response = self.client.post(
            "/api/complaints/",
            {"title": "Pothole", "description": "Deep road damage"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        complaint = Complaint.objects.get(pk=response.data["id"])
        self.assertIn("no contact email", complaint.department_email_error)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SEND_DEPARTMENT_EMAILS=True,
    )
    def test_pending_department_email_can_be_retried(self):
        complaint = self.make_complaint()
        self.roads.contact_email = "roads@example.gov.np"
        self.roads.save(update_fields=["contact_email"])
        call_command("send_pending_department_emails", verbosity=0)
        complaint.refresh_from_db()
        self.assertIsNotNone(complaint.department_email_sent_at)
        self.assertEqual(len(mail.outbox), 1)

    def test_complaint_lists_are_role_scoped(self):
        own = self.make_complaint()
        Complaint.objects.create(
            citizen=self.other_citizen,
            title="Water leak",
            description="Burst pipe",
            category=Complaint.Category.WATER_LEAKAGE,
            department=self.water,
        )

        self.client.force_authenticate(self.citizen)
        citizen_response = self.client.get("/api/complaints/")
        self.assertEqual(citizen_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in citizen_response.data["results"]], [own.id])

        self.client.force_authenticate(self.road_staff)
        staff_response = self.client.get("/api/complaints/")
        self.assertEqual([item["id"] for item in staff_response.data["results"]], [own.id])

    def test_other_department_cannot_change_status(self):
        complaint = self.make_complaint()
        self.client.force_authenticate(self.water_staff)
        response = self.client.patch(
            f"/api/complaints/{complaint.id}/status/",
            {"status": Complaint.Status.IN_PROGRESS},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_change_creates_history_and_citizen_notification(self):
        complaint = self.make_complaint()
        self.client.force_authenticate(self.road_staff)
        response = self.client.patch(
            f"/api/complaints/{complaint.id}/status/",
            {"status": Complaint.Status.IN_PROGRESS, "note": "Crew assigned"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            complaint.status_history.filter(
                status=Complaint.Status.IN_PROGRESS, changed_by=self.road_staff
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.citizen,
                complaint=complaint,
                kind=Notification.Kind.STATUS_CHANGE,
            ).exists()
        )

    def test_reopening_resolved_complaint_clears_resolved_timestamp(self):
        complaint = self.make_complaint()
        complaint.status = Complaint.Status.RESOLVED
        complaint.resolved_at = timezone.now()
        complaint.save()
        self.client.force_authenticate(self.road_staff)
        response = self.client.patch(
            f"/api/complaints/{complaint.id}/status/",
            {"status": Complaint.Status.IN_PROGRESS, "note": "More work required"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertIsNone(complaint.resolved_at)

    def test_repeating_same_status_does_not_duplicate_history(self):
        complaint = self.make_complaint()
        self.client.force_authenticate(self.road_staff)
        response = self.client.patch(
            f"/api/complaints/{complaint.id}/status/",
            {"status": Complaint.Status.PENDING},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(complaint.status_history.count(), 1)

    def test_missing_complaint_updates_return_404(self):
        self.client.force_authenticate(self.citizen)
        response = self.client.get("/api/complaints/999999/updates/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unrelated_citizen_cannot_read_complaint_updates(self):
        complaint = self.make_complaint()
        self.client.force_authenticate(self.other_citizen)
        response = self.client.get(f"/api/complaints/{complaint.id}/updates/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_department_update_notifies_citizen(self):
        complaint = self.make_complaint()
        self.client.force_authenticate(self.road_staff)
        response = self.client.post(
            f"/api/complaints/{complaint.id}/updates/",
            {"message": "Inspection is scheduled."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.citizen,
                complaint=complaint,
                kind=Notification.Kind.NEW_UPDATE,
            ).exists()
        )

    def test_dashboard_stats_are_role_scoped(self):
        self.make_complaint()
        Complaint.objects.create(
            citizen=self.other_citizen,
            title="Water leak",
            description="Burst pipe",
            category=Complaint.Category.WATER_LEAKAGE,
            department=self.water,
            is_emergency=True,
        )
        self.client.force_authenticate(self.citizen)
        response = self.client.get("/api/complaints/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["emergency"], 0)

    def test_sla_check_warns_admin_once_for_stale_complaint(self):
        complaint = self.make_complaint()
        Complaint.objects.filter(pk=complaint.pk).update(
            created_at=timezone.now() - timedelta(hours=49)
        )
        admin = User.objects.create_superuser(
            email="admin@example.com", password="StrongPassword!2026"
        )
        call_command("check_sla", verbosity=0)
        call_command("check_sla", verbosity=0)
        self.assertEqual(
            Notification.objects.filter(
                recipient=admin,
                complaint=complaint,
                kind=Notification.Kind.SLA_WARNING,
            ).count(),
            1,
        )
