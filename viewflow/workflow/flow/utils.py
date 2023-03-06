from functools import update_wrapper

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404
from viewflow.fsm import TransitionNotAllowed


def wrap_task_view(self, origin_view, permission=None):
    """Create wrapper around orig_view to inject request.activation."""

    def view(request, *args, **kwargs):
        process_pk, task_pk = kwargs.get("process_pk"), kwargs.get("task_pk")
        if process_pk is None or task_pk is None:
            raise ImproperlyConfigured(
                "Task view URL path should contain <int:process_pk> and <int:task_pk> parameters"
            )

        def call_with_activation():
            task = get_object_or_404(self.flow_class.task_class, pk=task_pk)
            request.activation = self.activation_class(task)

            if permission and not permission(request.user, task=task):
                raise PermissionDenied

            return origin_view(request, *args, **kwargs)

        try:
            if request.method == "POST":
                with transaction.atomic(), self.flow_class.lock(process_pk):
                    return call_with_activation()
            else:
                return call_with_activation()
        except TransitionNotAllowed as e:
            raise PermissionDenied(",".join(e.args))

    update_wrapper(view, origin_view)
    return view


def wrap_start_view(flow_task, origin_view):
    def view(request, *args, **kwargs):
        request.activation = flow_task.activation_class.create(flow_task, None, None)

        if not flow_task.can_execute(request.user, request.activation.task):
            raise PermissionDenied

        if request.method == "POST":
            with transaction.atomic():
                request.activation.start(request)
                return origin_view(request, *args, **kwargs)
        else:
            request.activation.start(request)
            return origin_view(request, *args, **kwargs)

    update_wrapper(view, origin_view)
    return view


def wrap_view(flow_task, origin_view):
    """Create wrapper around orig_view to inject request.activation."""

    def view(request, *args, **kwargs):
        process_pk, task_pk = kwargs.get("process_pk"), kwargs.get("task_pk")
        if process_pk is None or task_pk is None:
            raise ImproperlyConfigured(
                "Task view URL path should contain <int:process_pk> and <int:task_pk> parameters"
            )

        def call_with_activation():
            task = get_object_or_404(flow_task.flow_class.task_class, pk=task_pk)
            request.activation = flow_task.activation_class(task)

            if not flow_task.can_execute(request.user, task=task):
                raise PermissionDenied

            request.activation.start(request)
            return origin_view(request, *args, **kwargs)

        try:
            if request.method == "POST":
                with flow_task.flow_class.lock(process_pk), transaction.atomic():
                    return call_with_activation()
            else:
                return call_with_activation()
        except TransitionNotAllowed as e:
            raise PermissionDenied(",".join(e.args))

    update_wrapper(view, origin_view)
    return view
