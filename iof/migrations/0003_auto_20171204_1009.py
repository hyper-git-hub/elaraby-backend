# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-04 10:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0002_auto_20171121_0820'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticaggregations',
            name='last_updated',
            field=models.DateTimeField(db_index=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='logisticaggregations',
            name='online_status',
            field=models.BooleanField(default=False),
        ),
    ]
