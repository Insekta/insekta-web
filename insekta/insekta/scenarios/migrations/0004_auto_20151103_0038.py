# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('scenarios', '0003_auto_20151031_2047'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='solved_by',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True, related_name='solved_tasks'),
        ),
    ]
