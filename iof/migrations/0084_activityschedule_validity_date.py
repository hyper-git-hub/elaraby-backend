# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-10-12 06:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0083_auto_20201010_0751'),
    ]

    operations = [
        migrations.AddField(
            model_name='activityschedule',
            name='validity_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
