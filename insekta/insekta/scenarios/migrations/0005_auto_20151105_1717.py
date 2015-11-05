# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scenarios', '0004_auto_20151103_0038'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scenario',
            old_name='challenge',
            new_name='is_challenge',
        ),
    ]
