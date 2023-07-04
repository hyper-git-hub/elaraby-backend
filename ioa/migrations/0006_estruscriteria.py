# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-01-12 05:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0019_auto_20180112_0523'),
        ('ioa', '0005_auto_20180109_1038'),
    ]

    operations = [
        migrations.CreateModel(
            name='EstrusCriteria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modified_datetime', models.DateTimeField(blank=True, null=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('estrus_onset', models.BooleanField(default=False)),
                ('current_onset_datetime', models.DateTimeField(null=True)),
                ('current_off_datetime', models.DateTimeField(null=True)),
                ('last_onset_datetime', models.DateTimeField(null=True)),
                ('last_off_datetime', models.DateTimeField(null=True)),
                ('animal', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='estrus_animal_id', to='hypernet.Entity')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
