# Generated by Django 4.2.6 on 2023-11-25 04:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0005_products_margen"),
    ]

    operations = [
        migrations.AlterField(
            model_name="products",
            name="title",
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]