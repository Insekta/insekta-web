# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-25 01:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scenarios', '0014_scenariogroup_frontpage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, null=True)),
                ('enabled', models.BooleanField(default=False)),
                ('scenario_groups', models.ManyToManyField(to='scenarios.ScenarioGroup')),
            ],
        ),
    ]
