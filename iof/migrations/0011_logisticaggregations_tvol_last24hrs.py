# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-27 06:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0010_auto_20171221_1352'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticaggregations',
            name='tvol_last24Hrs',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=20, null=True),
        ),
    ]
