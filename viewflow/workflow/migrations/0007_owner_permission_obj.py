# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('viewflow', '0006_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='owner_permission_content_type',
            field=models.ForeignKey(blank=True, null=True, to='contenttypes.ContentType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='task',
            name='owner_permission_obj_pk',
            field=models.CharField(null=True, blank=True, max_length=255),
        ),
    ]
