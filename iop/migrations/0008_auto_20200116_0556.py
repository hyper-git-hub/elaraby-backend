# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-01-16 05:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('iop', '0007_energyconsumption'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iopderived',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='iop_device_derived', to='hypernet.Entity'),
        ),
    ]
