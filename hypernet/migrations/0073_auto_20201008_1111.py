# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-10-08 11:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0072_auto_20201006_1133'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hypernetnotification',
            name='value',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]