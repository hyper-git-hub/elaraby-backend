# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-26 09:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hypernet', '0061_invoicedata_invoice_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoicedata',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
