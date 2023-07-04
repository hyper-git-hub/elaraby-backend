# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-09-24 07:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0069_auto_20200116_1033'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='is_manual_mode',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='entity',
            name='is_washing_machine',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='entity',
            name='standby_mode',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
