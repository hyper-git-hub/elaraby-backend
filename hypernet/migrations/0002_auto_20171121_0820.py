# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-21 08:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user', '0001_initial'),
        ('options', '0001_initial'),
        ('customer', '0001_initial'),
        ('hypernet', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='roleassignmenthistory',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_assignment_modified_by_history', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='roleassignmenthistory',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_child_history', to='user.Role'),
        ),
        migrations.AddField(
            model_name='roleassignmenthistory',
            name='role_assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.RoleAssignment'),
        ),
        migrations.AddField(
            model_name='roleassignmenthistory',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='options.Options'),
        ),
        migrations.AddField(
            model_name='roleassignment',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='roleassignment',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entity_parent', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='roleassignment',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_assignment_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='roleassignment',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_child', to='user.Role'),
        ),
        migrations.AddField(
            model_name='roleassignment',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='options.Options'),
        ),
        migrations.AddField(
            model_name='hypernetpostdata',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='hypernetpostdata',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_data_device_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='hypernetpostdata',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='hypernetpostdata',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.DeviceType'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='animal',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_animal_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_data_device_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='driver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_driver_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='job',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_job_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='player',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notification_player_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='notification_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='hypernetnotification',
            name='violation_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notification_type_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='job_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_history_job_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='leased_owned',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_history_leased_owned_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='marital_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_history_marital_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_history_record_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='territory_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_history_territory_type_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entityhistory',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.DeviceType'),
        ),
        migrations.AddField(
            model_name='entityassociative',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='entityassociative',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='entityassociative',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='entity',
            name='breed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='animal_breed', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='contracted_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_contracted_type_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='entity',
            name='gender',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_gender_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='animal_group', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='job_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_job_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='lactation_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lactation_key', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='leased_owned',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_leased_owned_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='marital_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_marital_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='match_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_type_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='entity',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='entity',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entity_record_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='territory_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entity_training_type_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='entity',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.DeviceType'),
        ),
        migrations.AddField(
            model_name='deviceviolation',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='deviceviolation',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='violation_device_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='deviceviolation',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='deviceviolation',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='deviceviolation',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notification_record_status', to='options.Options'),
        ),
        migrations.AddField(
            model_name='deviceviolation',
            name='violation_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notification_violation_type', to='options.Options'),
        ),
        migrations.AddField(
            model_name='devicecalibration',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='devicecalibration',
            name='device',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calibration_device_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='devicecalibration',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calibration_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='devicecalibration',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='devicecalibration',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='options.Options'),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.Assignment'),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='child',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_child_history', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_history_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_parent_history', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='options.Options'),
        ),
        migrations.AddField(
            model_name='assignmenthistory',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.DeviceType'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='child',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_child', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_modified_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='assignment',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_parent', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='options.Options'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.DeviceType'),
        ),
    ]