# Generated by Django 4.2.6 on 2023-12-22 16:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pamo_bots", "0002_rename_products_productssodimac"),
    ]

    operations = [
        migrations.AddField(
            model_name="productssodimac",
            name="cod_barras",
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
