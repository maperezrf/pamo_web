# Generated by Django 4.2.6 on 2023-10-24 00:08

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("quote_print", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="quote",
            name="id_shopi",
        ),
        migrations.RemoveField(
            model_name="quote",
            name="updated_at",
        ),
    ]
