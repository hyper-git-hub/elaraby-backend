# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-08-20 10:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0004_auto_20180427_1608'),
        ('ffp', '0002_attendancerecord_employeeviolations'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='attendance_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='attendance_type', to='options.Options'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='check_out_dtm',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
