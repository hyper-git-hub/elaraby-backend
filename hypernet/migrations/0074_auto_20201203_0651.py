# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-12-03 06:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0073_auto_20201008_1111'),
    ]

    operations = [
        migrations.AddField(
            model_name='hypernetpostdata',
            name='cdt',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hypernetpostdata',
            name='clm',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hypernetpredata',
            name='cdt',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hypernetpredata',
            name='clm',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
