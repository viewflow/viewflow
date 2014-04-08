from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render


@transaction.atomic()
def start(request, start_task):
    if not start_task.has_perm(request.user):
        raise PermissionDenied

    activation = start_task.start(request.POST or None)

    if request.method == 'POST' and 'start' in request.POST:
        start_task.done(activation)

        activation.task.process.created_by = request.user
        activation.task.process.save()

        return redirect(reverse('viewflow:index', current_app=start_task.flow_cls._meta.namespace))

    return render(request, 'shipment/flow/start.html',
                  {'activation': activation})
