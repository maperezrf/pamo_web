# Generated by Django 4.2.6 on 2024-07-12 12:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pamo_bots", "0008_alter_productssodimac_rf_pamo_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="productssodimac",
            old_name="cod_barras",
            new_name="ean",
        ),
        migrations.RenameField(
            model_name="productssodimac",
            old_name="RF_pamo",
            new_name="sku_pamo",
        ),
        migrations.RenameField(
            model_name="productssodimac",
            old_name="SKU",
            new_name="sku_sodimac",
        ),
        migrations.RemoveField(
            model_name="productssodimac",
            name="Indicador",
        ),
    ]
