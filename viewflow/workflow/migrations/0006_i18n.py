# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import viewflow.workflow.token
import viewflow.workflow.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0005_rename_flowcls'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='process',
            options={'verbose_name_plural': 'Process list', 'ordering': ['-created'], 'verbose_name': 'Process'},
        ),
        migrations.AlterModelOptions(
            name='task',
            options={'verbose_name_plural': 'Tasks', 'ordering': ['-created'], 'verbose_name': 'Task'},
        ),
        migrations.AlterField(
            model_name='process',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='process',
            name='finished',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Finished'),
        ),
        migrations.AlterField(
            model_name='process',
            name='flow_class',
            field=viewflow.workflow.fields.FlowReferenceField(max_length=250, verbose_name='Flow'),
        ),
        migrations.AlterField(
            model_name='process',
            name='status',
            field=models.CharField(default='NEW', max_length=50, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='task',
            name='comments',
            field=models.TextField(blank=True, null=True, verbose_name='Comments'),
        ),
        migrations.AlterField(
            model_name='task',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created'),
        ),
        migrations.AlterField(
            model_name='task',
            name='external_task_id',
            field=models.CharField(blank=True, null=True, db_index=True, max_length=50, verbose_name='External Task ID'),
        ),
        migrations.AlterField(
            model_name='task',
            name='finished',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Finished'),
        ),
        migrations.AlterField(
            model_name='task',
            name='flow_task',
            field=viewflow.workflow.fields.TaskReferenceField(max_length=255, verbose_name='Task'),
        ),
        migrations.AlterField(
            model_name='task',
            name='flow_task_type',
            field=models.CharField(max_length=50, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='task',
            name='owner',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, blank=True, verbose_name='Owner', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='task',
            name='owner_permission',
            field=models.CharField(blank=True, null=True, max_length=255, verbose_name='Permission'),
        ),
        migrations.AlterField(
            model_name='task',
            name='previous',
            field=models.ManyToManyField(related_name='leading', to='viewflow.Task', verbose_name='Previous'),
        ),
        migrations.AlterField(
            model_name='task',
            name='process',
            field=models.ForeignKey(to='viewflow.Process', verbose_name='Process', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='task',
            name='started',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Started'),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(default='NEW', db_index=True, max_length=50, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='task',
            name='token',
            field=viewflow.workflow.fields.TokenField(default=viewflow.workflow.token.Token('start'), max_length=150, verbose_name='Token'),
        ),
    ]
