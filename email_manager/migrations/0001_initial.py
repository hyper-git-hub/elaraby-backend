# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-20 15:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('msg_title', models.CharField(max_length=255, null=True)),
                ('subject', models.CharField(max_length=255, null=True)),
                ('from_email', models.CharField(max_length=255)),
                ('description', models.TextField(null=True)),
                ('dtm', models.DateTimeField(null=True)),
                ('to_list', models.TextField(null=True)),
                ('cc_list', models.TextField(null=True)),
                ('bcc_list', models.TextField(null=True)),
                ('user_email_title', models.TextField(null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('placeholders', models.TextField(null=True)),
                ('email_type', models.CharField(
                    choices=[('internal', 'This email will be sent internally and can be mute from edit user. '),
                             ('external', 'This email will be sent to user & can be mute from notification settings.'),
                             ('system', "This email will be sent system wide and can't be mute.")], max_length=10)),
            ],
        ),
    ]
