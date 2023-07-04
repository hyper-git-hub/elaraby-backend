# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-24 07:17
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0024_hypernetnotification_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hypernetnotification',
            name='violation_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='notification_type_id', to='options.Options'),
        ),
    ]
