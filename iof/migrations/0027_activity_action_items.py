# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-16 12:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0026_auto_20180416_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='action_items',
            field=models.CharField(blank=True, max_length=5000, null=True),
        ),
    ]
