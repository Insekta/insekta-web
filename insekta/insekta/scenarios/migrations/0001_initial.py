# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('key', models.CharField(unique=True, max_length=120)),
                ('title', models.CharField(max_length=255)),
                ('challenge', models.BooleanField(default=False)),
                ('num_secrets', models.IntegerField()),
                ('enabled', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ScenarioGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('scenarios', models.ManyToManyField(to='scenarios.Scenario', related_name='groups')),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('identifier', models.CharField(max_length=120)),
                ('task_type', models.CharField(max_length=32)),
                ('scenario', models.ForeignKey(related_name='tasks', to='scenarios.Scenario')),
                ('solved_by', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='solved_tasks')),
            ],
        ),
    ]
