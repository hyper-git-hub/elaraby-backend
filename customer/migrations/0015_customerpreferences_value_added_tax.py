# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-03 10:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0014_customerpreferences_assets_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerpreferences',
            name='value_added_tax',
            field=models.FloatField(default=5),
        ),
    ]