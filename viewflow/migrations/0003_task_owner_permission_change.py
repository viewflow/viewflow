# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0002_fsmchange'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='owner_permission',
            field=models.CharField(blank=True, null=True, max_length=150),
        ),
    ]
