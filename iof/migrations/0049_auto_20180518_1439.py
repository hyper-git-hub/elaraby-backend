# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-18 09:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0043_auto_20180508_1344'),
        ('iof', '0048_auto_20180512_1327'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='activity_check_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_check_point', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activitydata',
            name='activity_check_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_data_activity_check_point', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activityqueue',
            name='activity_check_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_queue_activity_check_point', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activityschedule',
            name='activity_check_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_schedule_activity_check_point', to='hypernet.Entity'),
        ),
    ]
