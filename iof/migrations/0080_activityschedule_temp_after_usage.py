# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-30 06:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0079_bincollectiondata_timestamp_2'),
    ]

    operations = [
        migrations.AddField(
            model_name='activityschedule',
            name='temp_after_usage',
            field=models.FloatField(blank=True, null=True),
        ),
    ]