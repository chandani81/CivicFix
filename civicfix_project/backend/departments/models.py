from django.db import models


class Department(models.Model):
    """
    A government department that handles a category of complaints.
    e.g. Road Damage -> "Roads & Highways Department"
    """

    class Category(models.TextChoices):
        ROAD_DAMAGE = "road_damage", "Road Damage"
        WATER_LEAKAGE = "water_leakage", "Water Leakage"
        GARBAGE = "garbage", "Garbage"
        STREET_LIGHT = "street_light", "Street Light"
        DRAINAGE = "drainage", "Drainage"
        OTHERS = "others", "Others"

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=Category.choices, unique=True)
    description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
