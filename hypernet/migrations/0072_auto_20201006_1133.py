# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-10-06 11:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0071_auto_20200924_0756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='is_manual_mode',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='entity',
            name='is_washing_machine',
            field=models.NullBooleanField(default=False),
        ),
    ]