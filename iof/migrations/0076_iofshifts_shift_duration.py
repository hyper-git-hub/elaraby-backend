# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-02-22 10:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0075_iofshifts_trips'),
    ]

    operations = [
        migrations.AddField(
            model_name='iofshifts',
            name='shift_duration',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
