# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HelloWorldProcess',
            fields=[
                ('process_ptr', models.OneToOneField(to='viewflow.Process', primary_key=True, parent_link=True, serialize=False, auto_created=True)),
                ('text', models.CharField(max_length=50)),
                ('approved', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('viewflow.process',),
        ),
        migrations.CreateModel(
            name='HelloWorldTask',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('viewflow.task',),
        ),
    ]
