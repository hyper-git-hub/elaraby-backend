# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-31 10:04
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('iof', '0049_auto_20180518_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='created_datetime',
            field=models.DateTimeField(auto_now_add=True, db_index=True, default=datetime.datetime(2018, 5, 31, 10, 4, 42, 422962, tzinfo=utc)),
            preserve_default=False,
        ),
    ]