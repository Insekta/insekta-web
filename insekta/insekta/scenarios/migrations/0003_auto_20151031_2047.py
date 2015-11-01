# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scenarios', '0002_remove_task_task_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scenario',
            old_name='num_secrets',
            new_name='num_tasks',
        ),
    ]
