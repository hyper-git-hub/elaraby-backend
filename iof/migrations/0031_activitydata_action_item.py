# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-19 07:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0038_auto_20180418_1415'),
        ('iof', '0030_auto_20180418_1523'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitydata',
            name='action_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='action_item_id', to='hypernet.Entity'),
        ),
    ]
