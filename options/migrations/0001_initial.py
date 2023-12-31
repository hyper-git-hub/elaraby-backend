# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-21 08:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Options',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=50)),
                ('label', models.CharField(max_length=50)),
                ('label_en', models.CharField(max_length=50, null=True)),
                ('label_de', models.CharField(max_length=50, null=True)),
                ('label_pl', models.CharField(max_length=50, null=True)),
                ('label_it', models.CharField(max_length=50, null=True)),
                ('label_fr', models.CharField(max_length=50, null=True)),
            ],
        ),
    ]
