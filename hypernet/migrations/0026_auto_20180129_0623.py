# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-29 06:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0025_auto_20180124_0717'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hypernetnotification',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AlterField(
            model_name='hypernetnotification',
            name='driver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_driver_id', to='hypernet.Entity'),
        ),
        migrations.AlterField(
            model_name='hypernetnotification',
            name='job',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_job_id', to='hypernet.Entity'),
        ),
        migrations.AlterField(
            model_name='hypernetnotification',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='hypernetnotification',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='hypernetnotification',
            name='threshold',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='hypernetnotification',
            name='value',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=20, null=True),
        ),
    ]