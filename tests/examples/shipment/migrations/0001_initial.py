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
            name='Carrier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('phone', models.CharField(max_length=15)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Insurance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('company_name', models.CharField(max_length=50)),
                ('cost', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('shipment_no', models.CharField(max_length=50)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=75)),
                ('address', models.CharField(max_length=150)),
                ('city', models.CharField(max_length=150)),
                ('state', models.CharField(max_length=150)),
                ('zipcode', models.CharField(max_length=10)),
                ('country', models.CharField(max_length=150)),
                ('phone', models.CharField(max_length=50)),
                ('need_insurance', models.BooleanField(default=False)),
                ('carrier_quote', models.IntegerField(default=0)),
                ('post_label', models.TextField(blank=True, null=True)),
                ('package_tag', models.CharField(max_length=50)),
                ('carrier', models.ForeignKey(to='shipment.Carrier', null=True)),
                ('insurance', models.ForeignKey(to='shipment.Insurance', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShipmentItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=250)),
                ('quantity', models.IntegerField(default=1)),
                ('shipment', models.ForeignKey(to='shipment.Shipment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShipmentProcess',
            fields=[
                ('process_ptr', models.OneToOneField(to='viewflow.Process', parent_link=True, serialize=False, auto_created=True, primary_key=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, to=settings.AUTH_USER_MODEL)),
                ('shipment', models.ForeignKey(blank=True, null=True, to='shipment.Shipment')),
            ],
            options={
                'verbose_name_plural': 'Shipment process list',
                'permissions': [('can_start_request', 'Can start shipment request'), ('can_take_extra_insurance', 'Can take extra insurance'), ('can_package_goods', 'Can package goods'), ('can_move_package', 'Can move package')],
            },
            bases=('viewflow.process',),
        ),
        migrations.CreateModel(
            name='ShipmentTask',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('viewflow.task',),
        ),
    ]
