# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-03-15 10:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0065_entitydocument'),
    ]

    operations = [
        migrations.AddField(
            model_name='hypernetpostdata',
            name='raw_temperature',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AddField(
            model_name='hypernetpostdata',
            name='raw_volume',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
    ]
