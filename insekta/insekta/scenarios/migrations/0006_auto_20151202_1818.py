# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scenarios', '0005_auto_20151105_1717'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='num_tasks',
            field=models.IntegerField(default=0),
        ),
    ]
