# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-30 07:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0010_auto_20180528_2215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerpreferences',
            name='enable_accept_reject',
            field=models.BooleanField(default=True),
        ),
    ]
