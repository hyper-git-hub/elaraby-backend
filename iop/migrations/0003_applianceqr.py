# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-02-28 10:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iop', '0002_auto_20181221_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplianceQR',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ssid', models.CharField(max_length=200)),
                ('password', models.CharField(max_length=200)),
                ('device_id', models.CharField(max_length=200)),
            ],
        ),
    ]
