from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .base import (
    FlowManagePermissionMixin, BaseTaskActionView, get_task_hyperlink
)


class UndoView(FlowManagePermissionMixin, BaseTaskActionView):
    action_name = 'undo'

    def can_proceed(self):
        return self.activation.undo.can_proceed()

    def perform(self):
        self.activation.undo()
        hyperlink = get_task_hyperlink(self.activation.task, self.request.user)
        msg = _('Task {hyperlink} has been undone.').format(hyperlink=hyperlink)
        messages.info(self.request, mark_safe(msg), fail_silently=True)


class CancelView(FlowManagePermissionMixin, BaseTaskActionView):
    action_name = 'cancel'

    def can_proceed(self):
        return self.activation.cancel.can_proceed()

    def perform(self):
        self.activation.cancel()
        hyperlink = get_task_hyperlink(self.activation.task, self.request.user)
        msg = _('Task {hyperlink} has been canceled.').format(hyperlink=hyperlink)
        messages.info(self.request, mark_safe(msg), fail_silently=True)


class PerformView(FlowManagePermissionMixin, BaseTaskActionView):
    """Non-interactive task that cancelled and need to be started manually."""

    action_name = 'execute'

    def can_proceed(self):
        return self.activation.perform.can_proceed()

    def perform(self):
        self.activation.perform()
        hyperlink = get_task_hyperlink(self.activation.task, self.request.user)
        msg = _('Task {hyperlink} has been executed.').format(hyperlink=hyperlink)
        messages.success(self.request, mark_safe(msg), fail_silently=True)


class ActivateNextView(FlowManagePermissionMixin, BaseTaskActionView):
    """Activate next task without interactive task redone."""

    action_name = 'activate_next'

    def can_proceed(self):
        return self.activation.activate_next.can_proceed()

    def perform(self):
        self.activation.activate_next()
