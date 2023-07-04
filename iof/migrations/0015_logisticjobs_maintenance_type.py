# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-07 10:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0003_options_module'),
        ('iof', '0014_logisticjobs_notification_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticjobs',
            name='maintenance_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='logistic_maintenance_type_id', to='options.Options'),
        ),
    ]