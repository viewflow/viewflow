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
        migrations.AlterField(
            model_name='process',
            name='status',
            field=models.CharField(default='NEW', max_length=50),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='task',
            name='previous',
            field=models.ManyToManyField(related_name='leading', to='viewflow.Task'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(default='NEW', db_index=True, max_length=50),
            preserve_default=True,
        ),
    ]
