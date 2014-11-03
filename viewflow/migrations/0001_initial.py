# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django_fsm
import viewflow.fields
import viewflow.token


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('flow_cls', viewflow.fields.FlowReferenceField(max_length=250)),
                ('status', django_fsm.FSMField(choices=[('NEW', 'New'), ('STR', 'Stated'), ('FNS', 'Finished'), ('ERR', 'Error')], max_length=3, default='NEW')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('finished', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Process list',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('flow_task', viewflow.fields.TaskReferenceField(max_length=150)),
                ('flow_task_type', models.CharField(max_length=50)),
                ('status', django_fsm.FSMField(choices=[('NEW', 'New'), ('ASN', 'Assigned'), ('PRP', 'Prepared for execution'), ('STR', 'Stated'), ('FNS', 'Finished'), ('CNC', 'Cancelled'), ('ERR', 'Error')], max_length=3, db_index=True, default='NEW')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('started', models.DateTimeField(blank=True, null=True)),
                ('finished', models.DateTimeField(blank=True, null=True)),
                ('token', viewflow.fields.TokenField(max_length=150, default=viewflow.token.Token('start'))),
                ('external_task_id', models.CharField(blank=True, null=True, max_length=50, db_index=True)),
                ('owner_permission', models.CharField(blank=True, null=True, max_length=50)),
                ('owner', models.ForeignKey(null=True, blank=True, to=settings.AUTH_USER_MODEL)),
                ('previous', models.ManyToManyField(related_name='previous_rel_+', to='viewflow.Task')),
                ('process', models.ForeignKey(to='viewflow.Process')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
