# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion
import viewflow.workflow.token
import viewflow.workflow.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('flow_cls', viewflow.workflow.fields.FlowReferenceField(max_length=250)),
                ('status', models.CharField(max_length=50, default='NEW')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('finished', models.DateTimeField(blank=True, null=True)),
            ],
            options={'ordering': ['-created'], 'verbose_name_plural': 'Process list'},
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('flow_task', viewflow.workflow.fields.TaskReferenceField(max_length=150)),
                ('flow_task_type', models.CharField(max_length=50)),
                ('status', models.CharField(max_length=50, default='NEW', db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('started', models.DateTimeField(blank=True, null=True)),
                ('finished', models.DateTimeField(blank=True, null=True)),
                ('token', viewflow.workflow.fields.TokenField(max_length=150, default=viewflow.workflow.token.Token('start'))),
                ('external_task_id', models.CharField(max_length=50, null=True, blank=True, db_index=True)),
                ('owner_permission', models.CharField(max_length=50, blank=True, null=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=django.db.models.deletion.CASCADE)),
                ('previous', models.ManyToManyField(to='viewflow.Task', related_name='leading')),
                ('process', models.ForeignKey(to='viewflow.Process', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={'ordering': ['-created']},
        ),
    ]
