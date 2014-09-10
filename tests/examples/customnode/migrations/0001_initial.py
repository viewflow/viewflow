# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Decision',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('decision', models.BooleanField(default=False)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DynamicSplitProcess',
            fields=[
                ('process_ptr', models.OneToOneField(auto_created=True, to='viewflow.Process', serialize=False, primary_key=True)),
                ('split_count', models.IntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
            bases=('viewflow.process',),
        ),
        migrations.AddField(
            model_name='decision',
            name='process',
            field=models.ForeignKey(to='customnode.DynamicSplitProcess'),
            preserve_default=True,
        ),
    ]
