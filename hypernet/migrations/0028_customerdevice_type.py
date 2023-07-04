# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-08 09:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0027_auto_20180207_1657'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerdevice',
            name='type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='hypernet.DeviceType'),
            preserve_default=False,
        ),
    ]