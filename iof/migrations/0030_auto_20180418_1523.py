# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-18 10:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0038_auto_20180418_1415'),
        ('iof', '0029_activity_activity_start_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='acitvity_end_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_end_point', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activitydata',
            name='acitvity_end_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_data_end_point', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activityqueue',
            name='acitvity_end_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_queue_end_point', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activityschedule',
            name='acitvity_end_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_schedule_dumping_site', to='hypernet.Entity'),
        ),
        migrations.AlterField(
            model_name='activityschedule',
            name='primary_entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='activity_schedule_primary_entity', to='hypernet.Entity'),
        ),
    ]
