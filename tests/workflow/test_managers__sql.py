import sqlparse

from django.db import models
from django.db.models import Prefetch
from django.contrib.auth.models import User
from django.test import TestCase

from viewflow.workflow import flow, managers
from viewflow.workflow.models import Process, Task


class Test(TestCase):  # noqa: D101
    maxDiff = None

    def test_process_queryset_filter_by_flow_class_succeed(self):
        queryset = managers.ProcessQuerySet(model=Process).filter(flow_class=ChildFlow)

        self.assertEqual(
            str(queryset.query).strip(),
            'SELECT "viewflow_process"."id", "viewflow_process"."flow_class", "viewflow_process"."status",'
            ' "viewflow_process"."created", "viewflow_process"."finished", "viewflow_process"."data",'
            ' "viewflow_process"."parent_task_id", "viewflow_process"."seed_content_type_id",'
            ' "viewflow_process"."seed_object_id", "viewflow_process"."artifact_content_type_id",'
            ' "viewflow_process"."artifact_object_id" FROM "viewflow_process"'
            ' WHERE "viewflow_process"."flow_class" = tests/workflow.test_managers__sql.ChildFlow'
            ' ORDER BY "viewflow_process"."created" DESC',
        )

    def test_process_queryset_coerce_for_query(self):
        queryset = managers.ProcessQuerySet(model=Process).coerce_for([ChildFlow])

        self.assertEqual(
            sqlparse.format(str(queryset.query), reindent=True),
            'SELECT "viewflow_process"."id",\n'
            '       "viewflow_process"."flow_class",\n'
            '       "viewflow_process"."status",\n'
            '       "viewflow_process"."created",\n'
            '       "viewflow_process"."finished",\n'
            '       "viewflow_process"."data",\n'
            '       "viewflow_process"."parent_task_id",\n'
            '       "viewflow_process"."seed_content_type_id",\n'
            '       "viewflow_process"."seed_object_id",\n'
            '       "viewflow_process"."artifact_content_type_id",\n'
            '       "viewflow_process"."artifact_object_id",\n'
            '       "tests_childprocess"."process_ptr_id",\n'
            '       "tests_childprocess"."comment"\n'
            'FROM "viewflow_process"\n'
            'LEFT OUTER JOIN "tests_childprocess" ON ("viewflow_process"."id" = "tests_childprocess"."process_ptr_id")\n'
            'WHERE "viewflow_process"."flow_class" IN (tests/workflow.test_managers__sql.ChildFlow)\n'
            'ORDER BY "viewflow_process"."created" DESC',
        )

    def test_process_queryset_coerce_classes(self):
        process1 = ChildProcess.objects.create(flow_class=ChildFlow)
        process2 = GrandChildProcess.objects.create(flow_class=GrandChildFlow)

        with self.assertNumQueries(1):
            queryset = managers.ProcessQuerySet(model=Process).coerce_for(
                [GrandChildFlow, ChildFlow]
            )
            self.assertEqual(set(queryset), set([process1, process2]))

    def test_process_queryset_coerce_values_list(self):
        process = ChildProcess.objects.create(flow_class=ChildFlow)

        queryset = (
            managers.ProcessQuerySet(model=Process)
            .coerce_for([ChildFlow])
            .values_list("id")
        )
        self.assertEqual([(process.pk,)], list(queryset))

    def test_process_queryset_prefetch_related(self):
        process = ChildProcess.objects.create(flow_class=ChildFlow)

        # process -> participants
        queryset = (
            managers.ProcessQuerySet(model=Process)
            .coerce_for([ChildFlow])
            .prefetch_related(
                Prefetch("participants", queryset=User.objects.filter(is_staff=True))
            )
        )
        self.assertEqual([process], list(queryset))
        self.assertEqual([], list(queryset[0].participants.filter(is_staff=True)))

        # participants -> processes
        queryset = User.objects.filter(is_staff=True).prefetch_related(
            Prefetch("childprocess", queryset=ChildProcess.objects.all())
        )
        self.assertEqual([], list(queryset))

    def test_task_queryset_filter_by_flow_class_succeed(self):
        queryset = managers.TaskQuerySet(model=Task).filter(flow_task=ChildFlow.start)

        self.assertEqual(
            str(queryset.query).strip(),
            'SELECT "viewflow_task"."id", "viewflow_task"."flow_task", "viewflow_task"."flow_task_type",'
            ' "viewflow_task"."status", "viewflow_task"."created", "viewflow_task"."assigned",'
            ' "viewflow_task"."started", "viewflow_task"."finished", "viewflow_task"."token",'
            ' "viewflow_task"."external_task_id", "viewflow_task"."owner_id",'
            ' "viewflow_task"."owner_permission", "viewflow_task"."owner_permission_content_type_id",'
            ' "viewflow_task"."owner_permission_obj_pk", "viewflow_task"."process_id",'
            ' "viewflow_task"."data", "viewflow_task"."seed_content_type_id",'
            ' "viewflow_task"."seed_object_id", "viewflow_task"."artifact_content_type_id",'
            ' "viewflow_task"."artifact_object_id"'
            ' FROM "viewflow_task"'
            ' WHERE "viewflow_task"."flow_task" = tests/workflow.test_managers__sql.ChildFlow.start'
            ' ORDER BY "viewflow_task"."created" DESC',
        )

    def test_task_queryset_coerce_for_query(self):
        queryset = managers.TaskQuerySet(model=Task).coerce_for([ChildFlow])
        self.assertEqual(
            queryset.query.select_related, {"childtask": {}, "process": {}}
        )

        """
        Became broken under django 1.6 if file test_views_base have viewflow imports!

        self.assertEqual(str(queryset.query).strip(),
                         'SELECT "viewflow_task"."id", "viewflow_task"."flow_task", "viewflow_task"."flow_task_type",'
                         ' "viewflow_task"."status", "viewflow_task"."created", "viewflow_task"."started",'
                         ' "viewflow_task"."finished", "viewflow_task"."token", "viewflow_task"."process_id",'
                         ' "viewflow_task"."owner_id", "viewflow_task"."external_task_id",'
                         ' "viewflow_task"."owner_permission", "viewflow_task"."comments", "viewflow_process"."id",'
                         ' "viewflow_process"."flow_class", "viewflow_process"."status", "viewflow_process"."created",'
                         ' "viewflow_process"."finished", "tests_childtask"."task_ptr_id", "tests_childtask"."due_date"'
                         ' FROM "viewflow_task"'
                         ' INNER JOIN "viewflow_process" ON ( "viewflow_task"."process_id" = "viewflow_process"."id" )'
                         ' LEFT OUTER JOIN "tests_childtask" ON ( "viewflow_task"."id" = "tests_childtask"."task_ptr_id" )'
                         ' WHERE "viewflow_process"."flow_class" IN (tests/workflow.test_managers__sql.ChildFlow)')
        """

    def test_task_queryset_coerce_classes(self):
        process1 = ChildProcess.objects.create(flow_class=ChildFlow)
        process2 = GrandChildProcess.objects.create(flow_class=GrandChildFlow)

        task1 = ChildTask.objects.create(process=process1, flow_task=ChildFlow.start)
        task2 = Task.objects.create(process=process2, flow_task=GrandChildFlow.start)

        with self.assertNumQueries(1):
            queryset = managers.TaskQuerySet(model=Task).coerce_for(
                [GrandChildFlow, ChildFlow]
            )
            self.assertEqual(set(queryset), set([task1, task2]))

    def test_task_queryset_coerce_values_list(self):
        process = ChildProcess.objects.create(flow_class=ChildFlow)
        task = ChildTask.objects.create(process=process, flow_task=ChildFlow.start)

        queryset = (
            managers.TaskQuerySet(model=Task).coerce_for([ChildFlow]).values_list("id")
        )
        self.assertEqual([(task.pk,)], list(queryset))


class ChildProcess(Process):
    comment = models.CharField(max_length=50)
    participants = models.ManyToManyField(User)


class ChildTask(Task):
    due_date = models.DateTimeField(auto_now_add=True)


class GrandChildProcess(ChildProcess):
    description = models.TextField(max_length=50)


class ChildFlow(flow.Flow):
    process_class = ChildProcess
    task_class = ChildTask

    start = flow.Start(lambda request: None)


class GrandChildFlow(flow.Flow):
    process_class = GrandChildProcess

    start = flow.Start(lambda request: None)
