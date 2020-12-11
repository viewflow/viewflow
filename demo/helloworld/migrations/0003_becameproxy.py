from django.db import migrations
from django.db import connection


def copy_helloworld_data(apps, schema_editor):
    Process = apps.get_model("viewflow", "Process")

    with connection.cursor() as cursor:
        cursor.execute('select process_ptr_id, text, approved from helloworld_helloworldprocess') 
        for pk, text, approved in cursor.fetchall():
            process = Process.objects.get(pk=pk)
            process.data = {
                'text': text,
                'approved': approved,
            }
            process.save()


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0008_jsonfield_and_artifact'),
        ('helloworld', '0002_i18n'),
    ]

    operations = [
        migrations.RunPython(copy_helloworld_data),
        migrations.DeleteModel(
            name='HelloWorldProcess',
        ),
        migrations.CreateModel(
            name='HelloWorldProcess',
            fields=[
            ],
            options={
                'verbose_name': 'World Request',
                'verbose_name_plural': 'World Requests',
                'proxy': True,
                'indexes': [],
            },
            bases=('viewflow.process',),
        ),
    ]
