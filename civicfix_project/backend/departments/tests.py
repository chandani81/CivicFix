from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Department


User = get_user_model()


class DepartmentApiTests(APITestCase):
    def test_department_list_is_public_for_registration(self):
        Department.objects.create(name="Roads", category=Department.Category.ROAD_DAMAGE)
        response = self.client.get("/api/departments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_only_admin_can_create_department(self):
        citizen = User.objects.create_user(
            email="citizen@example.com", password="StrongPassword!2026"
        )
        payload = {"name": "Roads", "category": Department.Category.ROAD_DAMAGE}
        self.client.force_authenticate(citizen)
        forbidden = self.client.post("/api/departments/", payload, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        admin = User.objects.create_superuser(
            email="admin@example.com", password="StrongPassword!2026"
        )
        self.client.force_authenticate(admin)
        created = self.client.post("/api/departments/", payload, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)

    def test_admin_can_configure_department_routing_email(self):
        department = Department.objects.create(
            name="Roads", category=Department.Category.ROAD_DAMAGE
        )
        admin = User.objects.create_superuser(
            email="admin@example.com", password="StrongPassword!2026"
        )
        self.client.force_authenticate(admin)
        response = self.client.patch(
            f"/api/departments/{department.id}/",
            {"contact_email": "roads@example.gov.np"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        department.refresh_from_db()
        self.assertEqual(department.contact_email, "roads@example.gov.np")
