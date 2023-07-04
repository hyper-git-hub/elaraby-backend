# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-02-06 06:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0069_auto_20200116_1033'),
        ('iop', '0008_auto_20200116_0556'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorLogs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('date', models.DateField(auto_now_add=True, db_index=True)),
                ('inactive_score', models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.Entity')),
            ],
            options={
                'db_table': 'error_logs',
            },
        ),
    ]
