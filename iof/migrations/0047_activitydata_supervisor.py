# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-12 12:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0043_auto_20180508_1344'),
        ('iof', '0046_auto_20180510_1014'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitydata',
            name='supervisor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity_data_supervisor_id', to='hypernet.Entity'),
        ),
    ]