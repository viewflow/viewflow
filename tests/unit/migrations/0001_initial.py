# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import viewflow.token
import tests.unit.models
import viewflow.fields


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlowReferencedModel',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('flow_cls', viewflow.fields.FlowReferenceField(max_length=250)),
                ('task', viewflow.fields.TaskReferenceField(max_length=150, default=tests.unit.models.default)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestProcess',
            fields=[
                ('process_ptr', models.OneToOneField(auto_created=True, to='viewflow.Process', serialize=False, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('viewflow.process',),
        ),
        migrations.CreateModel(
            name='TokenModel',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('token', viewflow.fields.TokenField(max_length=150, default=viewflow.token.Token('start'))),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
