# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-07 09:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0006_auto_20180418_1415'),
        ('options', '0004_auto_20180427_1608'),
        ('user', '0009_auto_20180507_1101'),
        ('hypernet', '0041_remove_hypernetnotification_queue'),
        ('iof', '0041_activitydata_notes'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncidentReporting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('notes', models.CharField(blank=True, max_length=500, null=True)),
                ('action_items', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incident_action_items', to='hypernet.Entity')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incident_actor_id', to='hypernet.Entity')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer')),
                ('incident_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='incident_type_id', to='options.Options')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module')),
                ('primary_entity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incident_primary_entity_id', to='hypernet.Entity')),
                ('scheduled_activity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incident_schedule_id', to='iof.Activity')),
            ],
        ),
    ]
