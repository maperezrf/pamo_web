# Generated by Django 4.2.6 on 2023-10-23 22:59

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Quote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("id_shopi", models.CharField(max_length=50)),
                ("name", models.CharField(max_length=10)),
                ("customer", models.CharField(blank=True, max_length=50, null=True)),
                ("created_at", models.DateField()),
                ("updated_at", models.DateField()),
            ],
        ),
    ]
