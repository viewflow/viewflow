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
            name='Decision',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('decision', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='DynamicSplitProcess',
            fields=[
                ('process_ptr', models.OneToOneField(to='viewflow.Process', primary_key=True,
                                                     parent_link=True, serialize=False, auto_created=True,
                                                     on_delete=django.db.models.deletion.CASCADE)),
                ('question', models.CharField(max_length=50)),
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
            field=models.ForeignKey(to='customnode.DynamicSplitProcess', on_delete=django.db.models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='decision',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
