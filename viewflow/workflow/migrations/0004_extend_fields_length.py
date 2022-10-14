# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import viewflow.workflow.fields


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0003_task_owner_permission_change'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='flow_task',
            field=viewflow.workflow.fields.TaskReferenceField(max_length=255),
        ),
        migrations.AlterField(
            model_name='task',
            name='owner_permission',
            field=models.CharField(blank=True, null=True, max_length=255),
        )
    ]
