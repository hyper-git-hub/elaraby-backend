# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-16 05:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('options', '0003_options_module'),
        ('customer', '0003_customerclients_customerpreferences'),
        ('user', '0008_auto_20180416_1038'),
        ('hypernet', '0036_auto_20180416_1038'),
        ('iof', '0025_auto_20180413_1651'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_datetime', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('action_items', models.CharField(blank=True, max_length=5000, null=True)),
                ('activity_end_datetime', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BinCollectionData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pre_weight', models.FloatField(blank=True, null=True)),
                ('post_weight', models.FloatField(blank=True, null=True)),
                ('weight', models.FloatField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                ('invoice', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='IofShifts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shift_start_time', models.DateTimeField(auto_now_add=True, db_index=True, null=True)),
                ('shift_end_time', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts_child_id', to='hypernet.Entity')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.Customer')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Module')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts_parent_id', to='hypernet.Entity')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hypernet.DeviceType')),
            ],
        ),
        migrations.RemoveField(
            model_name='scheduledactivity',
            name='activity',
        ),
        migrations.RemoveField(
            model_name='scheduledactivity',
            name='primary_entity',
        ),
        migrations.RenameField(
            model_name='activity',
            old_name='activity',
            new_name='activity_schedule',
        ),
        migrations.RenameField(
            model_name='activityschedule',
            old_name='job_start_time',
            new_name='activity_start_time',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='user',
        ),
        migrations.RemoveField(
            model_name='activityschedule',
            name='activity',
        ),
        migrations.RemoveField(
            model_name='activityschedule',
            name='enable_accept_reject',
        ),
        migrations.RemoveField(
            model_name='activityschedule',
            name='end_datetime',
        ),
        migrations.RemoveField(
            model_name='activityschedule',
            name='secondary_entity',
        ),
        migrations.RemoveField(
            model_name='activityschedule',
            name='start_datetime',
        ),
        migrations.RemoveField(
            model_name='activityschedule',
            name='user',
        ),
        migrations.AddField(
            model_name='activityschedule',
            name='action_items',
            field=models.CharField(blank=True, max_length=5000, null=True),
        ),
        migrations.AddField(
            model_name='activityschedule',
            name='end_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='activityschedule',
            name='modified_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='schedule_modified_by', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='activityschedule',
            name='schedule_activity_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='scheduled_activity_status_id', to='options.Options'),
        ),
        migrations.AddField(
            model_name='activityschedule',
            name='start_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.DeleteModel(
            name='ScheduledActivity',
        ),
        migrations.AddField(
            model_name='bincollectiondata',
            name='activity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='iof.Activity'),
        ),
        migrations.AddField(
            model_name='bincollectiondata',
            name='bin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bin_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='bincollectiondata',
            name='truck',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_collection_device_id', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activityqueue',
            name='activity_schedule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='iof.ActivitySchedule'),
        ),
        migrations.AddField(
            model_name='activityqueue',
            name='actor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_activity_driver', to='hypernet.Entity'),
        ),
        migrations.AddField(
            model_name='activityqueue',
            name='primary_entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_activity_primary_entity', to='hypernet.Entity'),
        ),
    ]
