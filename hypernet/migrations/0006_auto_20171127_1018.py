# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-27 10:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0005_auto_20171124_0730'),
    ]

    operations = [
        migrations.CreateModel(
            name='Devices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('t_timestamp', models.DateTimeField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.Entity')),
            ],
        ),
        migrations.RenameField(
            model_name='hypernetpredata',
            old_name='harsh_acceleratioin',
            new_name='harsh_acceleration',
        ),
    ]
