from datetime import datetime

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition

from viewflow.fields import FlowReferenceField, TaskReferenceField


class Process(models.Model):
    class STATUS:
        NEW = 'NEW'
        STARTED = 'STR'
        FINISHED = 'FNS'
        ERROR = 'ERR'

    STATUS_CHOICES = ((STATUS.NEW, 'New'),
                      (STATUS.STARTED, 'Stated'),
                      (STATUS.FINISHED, 'Finished'),
                      (STATUS.ERROR, 'Error'))

    flow_cls = FlowReferenceField()
    status = FSMField(max_length=3, choices=STATUS_CHOICES, default=STATUS.NEW)

    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    @transition(field=status, source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        pass

    @transition(field=status, source=STATUS.STARTED, target=STATUS.FINISHED)
    def finish(self):
        self.finished = datetime.now()

    @transition(field=status, source=STATUS.STARTED, target=STATUS.ERROR)
    def error(self):
        pass

    @transition(field=status, source=STATUS.ERROR, target=STATUS.STARTED)
    def restart(self):
        pass

    def active_tasks(self):
        return Task.objects.filter(process=self, finished__isnull=True).order_by('created')


class Task(models.Model):
    class STATUS:
        NEW = 'NEW'
        ACTIVATED = 'ACT'
        ASSIGNED = 'ASN'
        STARTED = 'STR'
        FINISHED = 'FNS'
        CANCELLED = 'CNC'
        ERROR = 'ERR'

    STATUS_CHOICES = ((STATUS.NEW, 'New'),
                      (STATUS.ACTIVATED, 'Activated'),
                      (STATUS.ASSIGNED, 'Assigned'),
                      (STATUS.STARTED, 'Stated'),
                      (STATUS.FINISHED, 'Finished'),
                      (STATUS.CANCELLED, 'Cancelled'),
                      (STATUS.ERROR, 'Error'))

    process = models.ForeignKey(Process)
    flow_task = TaskReferenceField(flow_cls_ref='process__flow_cls')
    flow_task_type = models.CharField(max_length=50)
    status = FSMField(max_length=3, choices=STATUS_CHOICES, default=STATUS.NEW)

    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(blank=True, null=True)
    finished = models.DateTimeField(blank=True, null=True)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    owner_permission = models.CharField(max_length=50, blank=True, null=True)
    external_task_id = models.CharField(max_length=50, blank=True, null=True)
    previous = models.ManyToManyField('self')

    @transition(field=status, source=STATUS.NEW, target=STATUS.ACTIVATED)
    def activate(self):
        pass

    @transition(field=status, source=STATUS.ACTIVATED, target=STATUS.ASSIGNED)
    def assign(self, user):
        self.owner = user

    @transition(field=status, source=[STATUS.ACTIVATED, STATUS.ASSIGNED], target=STATUS.STARTED)
    def start(self, user=None, external_task_id=None):
        self.started = datetime.now()
        if user:
            self.owner = user
        if external_task_id:
            self.external_task_id = external_task_id

    @transition(field=status, source=STATUS.STARTED, target=STATUS.FINISHED)
    def done(self):
        self.finished = datetime.now()

    @transition(field=status, source=[STATUS.ACTIVATED, STATUS.STARTED], target=STATUS.CANCELLED)
    def cancel(self):
        self.finished = datetime.now()

    @transition(field=status, source=[STATUS.ACTIVATED, STATUS.STARTED], target=STATUS.ERROR)
    def error(self):
        pass

    def get_absolute_url(self):
        if self.process and self.flow_task:
            return self.process.flow_cls.instance.reverse(self)

    def save(self):
        if self.flow_task:
            self.flow_task_type = self.flow_task.task_type
        super(Task, self).save()
