# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-13 05:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0016_auto_20180713_1055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customerpreferences',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customerpreferences',
            name='email',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customerpreferences',
            name='fax_no',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customerpreferences',
            name='phone_no',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customerpreferences',
            name='url',
            field=models.TextField(blank=True, null=True),
        ),
    ]
