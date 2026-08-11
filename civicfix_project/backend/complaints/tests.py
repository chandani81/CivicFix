from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from departments.models import Department

from .models import Complaint, ComplaintUpdate


class ComplaintUpdateAccessTests(APITestCase):
    def setUp(self):
        self.assigned_department = Department.objects.create(
            name="Roads Department",
            category=Department.Category.ROAD_DAMAGE,
        )
        self.other_department = Department.objects.create(
            name="Water Department",
            category=Department.Category.WATER_LEAKAGE,
        )
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="StrongPass123!",
            role=User.Role.CITIZEN,
        )
        self.other_citizen = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            role=User.Role.CITIZEN,
        )
        self.assigned_staff = User.objects.create_user(
            email="roads@example.com",
            password="StrongPass123!",
            role=User.Role.DEPARTMENT,
            department=self.assigned_department,
        )
        self.other_staff = User.objects.create_user(
            email="water@example.com",
            password="StrongPass123!",
            role=User.Role.DEPARTMENT,
            department=self.other_department,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass123!",
            role=User.Role.ADMIN,
        )
        self.complaint = Complaint.objects.create(
            citizen=self.owner,
            title="Large pothole",
            description="A pothole is blocking the road.",
            category=Complaint.Category.ROAD_DAMAGE,
            department=self.assigned_department,
        )
        self.update = ComplaintUpdate.objects.create(
            complaint=self.complaint,
            posted_by=self.assigned_staff,
            message="Repair crew has been assigned.",
        )
        self.url = reverse("complaint-updates", kwargs={"pk": self.complaint.pk})

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_owner_can_list_updates(self):
        self.authenticate(self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.update.pk)

    def test_assigned_department_staff_can_list_updates(self):
        self.authenticate(self.assigned_staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_list_updates(self):
        self.authenticate(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unrelated_citizen_cannot_list_updates(self):
        self.authenticate(self.other_citizen)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unrelated_department_staff_cannot_list_updates(self):
        self.authenticate(self.other_staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_complaint_returns_not_found(self):
        self.authenticate(self.admin)
        url = reverse("complaint-updates", kwargs={"pk": 999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
