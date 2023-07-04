# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-04 06:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('customer', '0001_initial'),
        ('user', '0005_user_associated_entity'),
        ('ioa', '0002_auto_20171121_0820'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='animalstates',
            name='state_end_time',
        ),
        migrations.RemoveField(
            model_name='animalstates',
            name='state_start_time',
        ),
        migrations.RemoveField(
            model_name='animalstates',
            name='supervisor',
        ),
        migrations.AddField(
            model_name='animalstates',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ioa_customer',
                                    to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='animalstates',
            name='frequency',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='animalstates',
            name='module',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='animal_state_module', to='user.Module'),
        ),
        migrations.AlterField(
            model_name='animalstates',
            name='created_datetime',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='animalstates',
            name='device',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='customer_device_id', to='hypernet.CustomerDevice'),
        ),
    ]
