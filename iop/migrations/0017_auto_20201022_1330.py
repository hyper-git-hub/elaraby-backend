# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-10-22 13:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iop', '0016_auto_20201022_0955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reconfigurationtable',
            name='shs',
            field=models.IntegerField(default=3),
        ),
    ]
