# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-16 14:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0037_auto_20180416_1357'),
        ('iof', '0027_activity_action_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='primary_entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity_primary_entity', to='hypernet.Entity'),
        ),
    ]