from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from departments.models import Department


User = get_user_model()


class AccountApiTests(APITestCase):
    def setUp(self):
        self.roads = Department.objects.create(
            name="Roads", category=Department.Category.ROAD_DAMAGE
        )
        self.water = Department.objects.create(
            name="Water", category=Department.Category.WATER_LEAKAGE
        )

    def test_department_registration_requires_department(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "staff@example.com",
                "password": "StrongPassword!2026",
                "role": User.Role.DEPARTMENT,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("department", response.data)

    def test_citizen_registration_returns_login_session(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new.citizen@example.com",
                "password": "StrongPassword!2026",
                "first_name": "New",
                "role": User.Role.CITIZEN,
                "department": self.roads.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        user = User.objects.get(email="new.citizen@example.com")
        self.assertIsNone(user.department)

    def test_login_and_token_refresh(self):
        User.objects.create_user(
            email="login@example.com", password="StrongPassword!2026"
        )
        login = self.client.post(
            "/api/auth/login/",
            {"email": "login@example.com", "password": "StrongPassword!2026"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK, login.data)
        refreshed = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
        )
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK, refreshed.data)
        self.assertIn("access", refreshed.data)

    def test_citizen_cannot_move_themselves_to_a_department(self):
        citizen = User.objects.create_user(
            email="citizen@example.com", password="StrongPassword!2026"
        )
        self.client.force_authenticate(citizen)
        response = self.client.patch(
            "/api/auth/me/", {"department": self.roads.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        citizen.refresh_from_db()
        self.assertIsNone(citizen.department)

    def test_admin_can_reassign_department_staff(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password="StrongPassword!2026"
        )
        staff = User.objects.create_user(
            email="staff@example.com",
            password="StrongPassword!2026",
            role=User.Role.DEPARTMENT,
            department=self.roads,
        )
        self.client.force_authenticate(admin)
        response = self.client.patch(
            f"/api/auth/staff/{staff.id}/",
            {"department": self.water.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        staff.refresh_from_db()
        self.assertEqual(staff.department, self.water)

    def test_non_admin_cannot_list_staff(self):
        citizen = User.objects.create_user(
            email="citizen@example.com", password="StrongPassword!2026"
        )
        self.client.force_authenticate(citizen)
        response = self.client.get("/api/auth/staff/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
