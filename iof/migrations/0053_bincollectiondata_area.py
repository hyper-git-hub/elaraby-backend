# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-12 12:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0051_auto_20180703_1645'),
        ('iof', '0052_auto_20180706_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='bincollectiondata',
            name='area',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity_area_id', to='hypernet.Entity'),
        ),
    ]
