# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-10-12 07:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0084_activityschedule_validity_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activityschedule',
            name='validity_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
