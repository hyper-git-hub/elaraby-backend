# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-20 05:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0012_devicecalibration_calibration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='devicecalibration',
            name='calibration',
            field=models.CharField(blank=True, max_length=9000000, null=True),
        ),
    ]
