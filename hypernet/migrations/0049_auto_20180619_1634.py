# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-19 11:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0048_auto_20180611_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='volume_capacity',
            field=models.FloatField(blank=True, null=True),
        ),
    ]