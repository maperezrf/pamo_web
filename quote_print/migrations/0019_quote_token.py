import uuid
from django.db import migrations, models


def populate_tokens(apps, schema_editor):
    Quote = apps.get_model('quote_print', 'Quote')
    for quote in Quote.objects.filter(token__isnull=True):
        quote.token = uuid.uuid4()
        quote.save(update_fields=['token'])


class Migration(migrations.Migration):

    dependencies = [
        ('quote_print', '0018_sodimacorders_oc_shopify'),
    ]

    operations = [
        # Step 1: add nullable, non-unique so existing rows are accepted
        migrations.AddField(
            model_name='quote',
            name='token',
            field=models.UUIDField(null=True),
        ),
        # Step 2: fill existing rows with unique UUIDs
        migrations.RunPython(populate_tokens, migrations.RunPython.noop),
        # Step 3: enforce unique + not null
        migrations.AlterField(
            model_name='quote',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
