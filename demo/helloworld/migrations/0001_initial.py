# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HelloWorldProcess',
            fields=[
                ('process_ptr', models.OneToOneField(to='viewflow.Process', primary_key=True, parent_link=True, serialize=False, auto_created=True, on_delete=django.db.models.deletion.CASCADE)),
                ('text', models.CharField(max_length=50)),
                ('approved', models.BooleanField(default=False)),
            ],
            options={'verbose_name': 'Hello Request'},
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
