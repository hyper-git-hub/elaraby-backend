# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-20 09:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0049_auto_20180619_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='name',
            field=models.CharField(max_length=1000),
        ),
    ]
