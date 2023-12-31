# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-04-11 08:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0026_customerpreferences_diesel_price'),
        ('hypernet', '0066_auto_20190315_1046'),
        ('user', '0011_auto_20180530_1007'),
        ('iop', '0004_remove_applianceqr_device_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='IopAggregation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_errors', models.IntegerField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                ('online_status', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer')),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='iop_device_aggregation', to='hypernet.Entity')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module')),
            ],
        ),
        migrations.AlterField(
            model_name='iopderived',
            name='timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
