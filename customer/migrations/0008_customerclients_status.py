# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-09 07:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0004_auto_20180427_1608'),
        ('customer', '0007_auto_20180509_1134'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerclients',
            name='status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='options.Options'),
            preserve_default=False,
        ),
    ]
