"""
Seeds demo accounts and a couple of sample complaints so you have
something to show immediately for your defense, without manually
registering through the API first.

Usage:
    python manage.py seed_demo
"""

from django.core.management.base import BaseCommand

from accounts.models import User
from complaints.models import Complaint, ComplaintStatusHistory
from departments.models import Department


class Command(BaseCommand):
    help = "Seeds demo admin/department/citizen accounts and sample complaints."

    def handle(self, *args, **options):
        # 1. Admin
        admin, created = User.objects.get_or_create(
            email="admin@civicfix.local",
            defaults=dict(role=User.Role.ADMIN, is_staff=True, is_superuser=True, first_name="Site", last_name="Admin"),
        )
        if created:
            admin.set_password("Admin@12345")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin@civicfix.local / Admin@12345"))

        # 2. Departments (in case seed_departments wasn't run yet)
        from django.core.management import call_command
        call_command("seed_departments")

        road_dept = Department.objects.get(category=Department.Category.ROAD_DAMAGE)

        # 3. Department staff
        staff, created = User.objects.get_or_create(
            email="roads.staff@civicfix.local",
            defaults=dict(role=User.Role.DEPARTMENT, department=road_dept, first_name="Roads", last_name="Staff"),
        )
        if created:
            staff.set_password("Staff@12345")
            staff.save()
            self.stdout.write(self.style.SUCCESS("Created roads.staff@civicfix.local / Staff@12345"))

        # 4. Citizen
        citizen, created = User.objects.get_or_create(
            email="citizen@civicfix.local",
            defaults=dict(role=User.Role.CITIZEN, first_name="Demo", last_name="Citizen"),
        )
        if created:
            citizen.set_password("Citizen@12345")
            citizen.save()
            self.stdout.write(self.style.SUCCESS("Created citizen@civicfix.local / Citizen@12345"))

        # 5. Sample complaint
        if not Complaint.objects.filter(title="Large pothole on Ring Road").exists():
            complaint = Complaint.objects.create(
                citizen=citizen,
                title="Large pothole on Ring Road",
                description="A deep pothole near the Koteshwor junction is causing bike accidents.",
                category=Complaint.Category.ROAD_DAMAGE,
                department=road_dept,
                status=Complaint.Status.PENDING,
                address="Koteshwor, Kathmandu",
            )
            ComplaintStatusHistory.objects.create(
                complaint=complaint, status=Complaint.Status.PENDING, changed_by=citizen, note="Complaint submitted."
            )
            self.stdout.write(self.style.SUCCESS(f"Created sample complaint #{complaint.id}"))

        self.stdout.write(self.style.SUCCESS("\nDemo seed complete."))
        self.stdout.write("Login with:")
        self.stdout.write("  Admin:      admin@civicfix.local / Admin@12345")
        self.stdout.write("  Department: roads.staff@civicfix.local / Staff@12345")
        self.stdout.write("  Citizen:    citizen@civicfix.local / Citizen@12345")
