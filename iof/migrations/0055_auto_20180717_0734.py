# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-17 07:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0054_activityschedule_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activitydata',
            name='scheduled_activity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity_template_id', to='iof.Activity'),
        ),
    ]
