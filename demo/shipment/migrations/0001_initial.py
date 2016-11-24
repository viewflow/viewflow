# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Carrier',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('phone', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Insurance',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('company_name', models.CharField(max_length=50)),
                ('cost', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('shipment_no', models.CharField(max_length=50)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
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
                ('carrier', models.ForeignKey(to='shipment.Carrier', null=True, on_delete=django.db.models.deletion.CASCADE)),
                ('insurance', models.ForeignKey(to='shipment.Insurance', null=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentItem',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('quantity', models.IntegerField(default=1)),
                ('shipment', models.ForeignKey(to='shipment.Shipment', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentProcess',
            fields=[
                ('process_ptr', models.OneToOneField(to='viewflow.Process', primary_key=True, parent_link=True, serialize=False, auto_created=True, on_delete=django.db.models.deletion.CASCADE)),
                ('shipment', models.ForeignKey(blank=True, to='shipment.Shipment', null=True, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'permissions': [('can_start_request', 'Can start shipment request'), ('can_take_extra_insurance', 'Can take extra insurance'), ('can_package_goods', 'Can package goods'), ('can_move_package', 'Can move package')],
                'verbose_name_plural': 'Shipment process list',
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
