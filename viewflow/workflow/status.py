from django.db import models
from django.utils.translation import pgettext_lazy


class PROCESS(models.TextChoices):
    CANCELED = 'CANCELED', pgettext_lazy('STATUS', 'Canceled')
    DONE = 'DONE', pgettext_lazy('STATUS', 'Done')
    NEW = 'NEW', pgettext_lazy('STATUS', 'New')


class STATUS(models.TextChoices):
    ASSIGNED = 'ASSIGNED', pgettext_lazy('STATUS', 'Assigned')
    CANCELED = 'CANCELED', pgettext_lazy('STATUS', 'Canceled')
    DONE = 'DONE', pgettext_lazy('STATUS', 'Done')
    ERROR = 'ERROR', pgettext_lazy('STATUS', 'Error')
    NEW = 'NEW', pgettext_lazy('STATUS', 'New')
    REVIVED = 'REVIVED', pgettext_lazy('STATUS', 'Revived')  # TODO
    SCHEDULED = 'SCHEDULED', pgettext_lazy('STATUS', 'Scheduled')
    STARTED = 'STARTED', pgettext_lazy('STATUS', 'Started')

    def __str__(self):
        return str(self.value)
