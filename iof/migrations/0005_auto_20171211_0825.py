# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-11 08:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0004_logisticaggregations_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticaggregations',
            name='last_density',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='logisticaggregations',
            name='last_latitude',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='logisticaggregations',
            name='last_longitude',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='logisticaggregations',
            name='last_speed',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='logisticaggregations',
            name='last_temperature',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='logisticaggregations',
            name='last_volume',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
    ]
