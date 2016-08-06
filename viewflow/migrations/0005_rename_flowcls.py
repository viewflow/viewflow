# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0004_extend_fields_length'),
    ]

    operations = [
        migrations.RenameField(
            model_name='process',
            old_name='flow_cls',
            new_name='flow_class',
        ),
    ]
