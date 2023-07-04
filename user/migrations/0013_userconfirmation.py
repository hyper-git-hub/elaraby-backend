# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-12-07 10:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_auto_20200129_0807'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserConfirmation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('contact_number', models.CharField(blank=True, max_length=30, null=True)),
                ('reset_token', models.CharField(blank=True, max_length=50)),
            ],
        ),
    ]
