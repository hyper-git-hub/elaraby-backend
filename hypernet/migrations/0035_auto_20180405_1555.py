# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-05 10:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0034_auto_20180405_1203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hypernetnotification',
            name='title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]