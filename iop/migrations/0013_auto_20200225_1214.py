# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-02-25 12:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iop', '0012_reconfigurationtable'),
    ]

    operations = [
        migrations.AddField(
            model_name='reconfigurationtable',
            name='temperature_set',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='reconfigurationtable',
            name='failure_code',
            field=models.IntegerField(default=0),
        ),
    ]
