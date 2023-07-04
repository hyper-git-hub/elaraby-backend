# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-03 10:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0033_auto_20180305_0531'),
        ('iof', '0016_auto_20180402_1618'),
    ]

    operations = [
        migrations.AddField(
            model_name='activityschedule',
            name='actor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='driver_id', to='hypernet.Entity'),
        ),
    ]