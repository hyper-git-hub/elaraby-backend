# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-27 11:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('options', '0003_options_module'),
    ]

    operations = [
        migrations.AlterField(
            model_name='options',
            name='key',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='options',
            name='label',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='options',
            name='label_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='options',
            name='label_fr',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='options',
            name='value',
            field=models.CharField(max_length=100),
        ),
    ]
