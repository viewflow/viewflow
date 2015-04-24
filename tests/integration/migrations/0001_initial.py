# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrokenGateProcess',
            fields=[
                ('process_ptr', models.OneToOneField(primary_key=True, serialize=False, parent_link=True, auto_created=True, to='viewflow.Process')),
                ('throw_error', models.BooleanField(default=False)),
            ],
            bases=('viewflow.process',),
        ),
        migrations.CreateModel(
            name='TestCeleryProcess',
            fields=[
                ('process_ptr', models.OneToOneField(primary_key=True, serialize=False, parent_link=True, auto_created=True, to='viewflow.Process')),
                ('throw_error', models.BooleanField(default=False)),
            ],
            bases=('viewflow.process',),
        ),
    ]
