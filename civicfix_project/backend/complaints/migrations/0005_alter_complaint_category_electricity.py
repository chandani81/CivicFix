from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("departments", "0002_electricity_department_label"),
        ("complaints", "0004_complaint_department_email_audit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complaint",
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
            ),
        ),
    ]
