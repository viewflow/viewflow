from django.db import migrations, models
from django.db.models import Q


def remove_task_check_constraints(apps, schema_editor):
    Task = apps.get_model("viewflow", "Task")

    schema_editor.remove_constraint(Task, "check_artifact_object_id")
    schema_editor.remove_constraint(Task, "check_seed_object_id")


def add_task_check_constraints(apps, schema_editor):
    Task = apps.get_model("viewflow", "Task")

    schema_editor.add_constraint(
        Task,
        models.CheckConstraint(
            name="check_artifact_object_id",
            condition=Q(artifact_object_id__gte=0),
        )
    )
    schema_editor.add_constraint(
        Task,
        models.CheckConstraint(
            name="check_seed_object_id",
            condition=Q(seed_object_id__gte=0),
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ("viewflow", "0014_alter_process_parent_task"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="process",
                    name="artifact_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),
                migrations.AlterField(
                    model_name="process",
                    name="seed_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),
                migrations.AlterField(
                    model_name="task",
                    name="artifact_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),
                migrations.AlterField(
                    model_name="task",
                    name="seed_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),
            ],
            database_operations=[
                # Not all databases support altering the column type for
                # columns that are part of an index, so remove the index
                # first...
                migrations.RemoveIndex(
                    model_name="process",
                    name="viewflow_pr_artifac_64c8a3_idx",
                ),

                # ... then alter the columns ...
                migrations.AlterField(
                    model_name="process",
                    name="artifact_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),
                migrations.AlterField(
                    model_name="process",
                    name="seed_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),

                # ... and recreate afterward.
                migrations.AddIndex(
                    model_name="process",
                    index=models.Index(
                        fields=["artifact_content_type", "artifact_object_id"],
                        name="viewflow_pr_artifac_64c8a3_idx",
                    ),
                ),

                # Not all databases support altering the column type for
                # columns with constraints, so remove the constraints first ...
                migrations.RunPython(remove_task_check_constraints),

                # ... then alter the columns ...
                migrations.AlterField(
                    model_name="task",
                    name="artifact_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),

                migrations.AlterField(
                    model_name="task",
                    name="seed_object_id",
                    field=models.CharField(blank=True, max_length=36, null=True),
                ),

                # ... and recreate afterward.
                migrations.RunPython(add_task_check_constraints),
            ],
        ),
    ]
