from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('hypernet', '0066_auto_20190315_1046'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='is_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
