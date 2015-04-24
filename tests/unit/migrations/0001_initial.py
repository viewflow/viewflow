# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import viewflow.fields
import tests.unit.models
import viewflow.token


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlowReferencedModel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('flow_cls', viewflow.fields.FlowReferenceField(max_length=250)),
                ('task', viewflow.fields.TaskReferenceField(max_length=150, default=tests.unit.models.default)),
            ],
        ),
        migrations.CreateModel(
            name='TestProcess',
            fields=[
                ('process_ptr', models.OneToOneField(to='viewflow.Process', primary_key=True, serialize=False, auto_created=True, parent_link=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('viewflow.process',),
        ),
        migrations.CreateModel(
            name='TokenModel',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('token', viewflow.fields.TokenField(max_length=150, default=viewflow.token.Token('start'))),
            ],
        ),
    ]
