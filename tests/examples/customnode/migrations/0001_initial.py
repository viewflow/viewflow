# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Decision',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('decision', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DynamicSplitProcess',
            fields=[
                ('process_ptr', models.OneToOneField(primary_key=True, to='viewflow.Process', parent_link=True, auto_created=True, serialize=False)),
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
        migrations.AddField(
            model_name='decision',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True),
            preserve_default=True,
        ),
    ]
