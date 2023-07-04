# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-14 06:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customer', '0025_auto_20181129_0817'),
        ('hypernet', '0059_entity_skip_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='IopDerived',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('total_errors', models.IntegerField(blank=True, default=0, null=True)),
                ('active_duration', models.IntegerField(blank=True, default=0, null=True)),
                ('total_energy_consumed', models.IntegerField(blank=True, default=0, null=True)),
                ('average_temperature', models.DecimalField(blank=True, decimal_places=3, max_digits=3, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='iop_device_derived', to='hypernet.Entity')),
            ],
        ),
    ]
