# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-17 06:26
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0021_deviceviolation_next_trigger_datetime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceviolation',
            name='modified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_modified_by', to=settings.AUTH_USER_MODEL),
        ),
    ]