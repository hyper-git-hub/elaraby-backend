# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-17 12:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ffp', '0011_employeeviolations_active_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='active_status',
            field=models.BooleanField(default=False),
        ),
    ]
