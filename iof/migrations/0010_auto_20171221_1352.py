# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-21 13:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0009_auto_20171220_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logisticjobs',
            name='job_start_timestamp',
            field=models.DateTimeField(db_index=True),
        ),
    ]
