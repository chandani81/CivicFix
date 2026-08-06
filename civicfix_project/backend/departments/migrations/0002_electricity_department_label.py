from django.db import migrations, models


def rename_electricity_department(apps, schema_editor):
    Department = apps.get_model("departments", "Department")
    Department.objects.filter(category="street_light").update(
        name="Electricity Department",
        description=(
            "Handles electricity supply, poles, exposed wires, transformers, "
            "and public lighting complaints."
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("departments", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="department",
            name="category",
            field=models.CharField(
                choices=[
                    ("road_damage", "Road Damage"),
                    ("water_leakage", "Water Leakage"),
                    ("garbage", "Garbage"),
                    ("street_light", "Electricity"),
                    ("drainage", "Drainage"),
                    ("others", "Others"),
                ],
                max_length=30,
                unique=True,
            ),
        ),
        migrations.RunPython(rename_electricity_department, migrations.RunPython.noop),
    ]
