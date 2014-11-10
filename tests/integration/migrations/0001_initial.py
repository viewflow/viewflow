# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestCeleryProcess',
            fields=[
                ('process_ptr', models.OneToOneField(parent_link=True, serialize=False, primary_key=True, to='viewflow.Process', auto_created=True)),
                ('throw_error', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=('viewflow.process',),
        ),
    ]
