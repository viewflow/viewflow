# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='comments',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
    ]
