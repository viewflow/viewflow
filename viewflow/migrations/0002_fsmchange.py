from django.db import models, migrations

def rollback_status_update(apps, schema_editor):
    Task = apps.get_model("viewflow", "Task")
    Task.objects.filter(status='DONE').update(status='FNS')
    Task.objects.filter(status='STARTED').update(status='STR')
    Task.objects.filter(status='ASSIGNED').update(status='ASN')

    Process = apps.get_model("viewflow", "Process")
    Process.objects.filter(status='DONE').update(status='FNS')
    Process.objects.filter(status='STARTED').update(status='STR')

def update_status(apps, schema_editor):
    Process = apps.get_model("viewflow", "Process")
    Process.objects.filter(status='STR').update(status='STARTED')
    Process.objects.filter(status='FNS').update(status='DONE')

    Task = apps.get_model("viewflow", "Task")
    Task.objects.filter(status='ASN').update(status='ASSIGNED')
    Task.objects.filter(status='STR').update(status='STARTED')
    Task.objects.filter(status='FNS').update(status='DONE')


class Migration(migrations.Migration):

    dependencies = [
        ('viewflow', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='comments',
            field=models.TextField(blank=True, null=True),
            preserve_default=True,
        ),
        migrations.RunPython(
            update_status, reverse_code=rollback_status_update
        )
    ]
