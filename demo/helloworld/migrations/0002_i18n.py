# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('helloworld', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HelloWorldTask',
        ),
        migrations.AlterModelOptions(
            name='helloworldprocess',
            options={'verbose_name': 'World Request', 'verbose_name_plural': 'World Requests'},
        ),
        migrations.AlterField(
            model_name='helloworldprocess',
            name='approved',
            field=models.BooleanField(default=False, verbose_name='Approved'),
        ),
        migrations.AlterField(
            model_name='helloworldprocess',
            name='text',
            field=models.CharField(verbose_name='Message', max_length=50),
        ),
    ]
