# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-25 05:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0006_auto_20180418_1415'),
        ('user', '0008_auto_20180416_1038'),
        ('iof', '0034_activitydata_created_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='customer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='activity',
            name='module',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='activitydata',
            name='customer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='activitydata',
            name='module',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='activityqueue',
            name='customer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='activityqueue',
            name='module',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bincollectiondata',
            name='customer',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='customer.Customer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bincollectiondata',
            name='module',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='user.Module'),
            preserve_default=False,
        ),
    ]
