# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-01-24 07:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0004_auto_20180427_1608'),
        ('iof', '0066_auto_20190124_1157'),
    ]

    operations = [
        migrations.AddField(
            model_name='activityqueue',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='queue_type_id', to='options.Options'),
        ),
    ]
