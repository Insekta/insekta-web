# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-18 21:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('remoteapi', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='vmresourcedummy',
            old_name='resource',
            new_name='resource_name',
        ),
    ]
