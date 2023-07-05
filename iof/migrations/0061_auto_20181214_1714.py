# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-14 12:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0060_auto_20181213_1219'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logisticsderived',
            name='post_dec_vol',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='logisticsderived',
            name='post_fill_vol',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='logisticsderived',
            name='pre_dec_vol',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='logisticsderived',
            name='pre_fill_vol',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
    ]