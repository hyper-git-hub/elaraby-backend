# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-04-15 11:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0078_cmsvehiclereporting'),
    ]

    operations = [
        migrations.AddField(
            model_name='bincollectiondata',
            name='timestamp_2',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
