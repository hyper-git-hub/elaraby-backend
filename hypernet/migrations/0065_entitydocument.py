# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-03-07 10:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0064_userentityassignment_is_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='documents/')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.Entity')),
            ],
        ),
    ]
