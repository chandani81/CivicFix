from django.core.management.base import BaseCommand

from departments.models import Department

DEFAULT_DEPARTMENTS = [
    {
        "name": "Roads & Highways Department",
        "category": Department.Category.ROAD_DAMAGE,
        "description": "Handles potholes, broken pavement, and road damage complaints.",
        "contact_email": "roads@civicfix.local",
    },
    {
        "name": "Water Supply Department",
        "category": Department.Category.WATER_LEAKAGE,
        "description": "Handles water leakage and water supply issues.",
        "contact_email": "water@civicfix.local",
    },
    {
        "name": "Sanitation & Waste Management Department",
        "category": Department.Category.GARBAGE,
        "description": "Handles garbage collection and cleanliness complaints.",
        "contact_email": "sanitation@civicfix.local",
    },
    {
        "name": "Electricity Department",
        "category": Department.Category.STREET_LIGHT,
        "description": "Handles electricity supply, poles, exposed wires, transformers, and public lighting complaints.",
        "contact_email": "electricity@civicfix.local",
    },
    {
        "name": "Drainage & Sewerage Department",
        "category": Department.Category.DRAINAGE,
        "description": "Handles blocked or damaged drainage systems.",
        "contact_email": "drainage@civicfix.local",
    },
    {
        "name": "General Municipal Affairs Department",
        "category": Department.Category.OTHERS,
        "description": "Handles complaints that don't fit any other category.",
        "contact_email": "general@civicfix.local",
    },
]


class Command(BaseCommand):
    help = "Seed the default departments (Road Damage, Water Leakage, Garbage, Electricity, Drainage, Others)."

    def handle(self, *args, **options):
        created_count = 0
        for dept in DEFAULT_DEPARTMENTS:
            obj, created = Department.objects.get_or_create(
                category=dept["category"], defaults=dept
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {obj.name}"))
            else:
                self.stdout.write(f"Already exists: {obj.name}")

        self.stdout.write(self.style.SUCCESS(f"\nDone. {created_count} department(s) created."))
