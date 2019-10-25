from django.urls import reverse

try:
    # django 3.0+
    from django.utils.http import url_has_allowed_host_and_scheme as is_safe_url
except ImportError:
    from django.utils.http import is_safe_url

from ... import activation


def get_next_task_url(request, process):
    """Heuristic for user on complete task redirect."""
    namespace = request.resolver_match.namespace

    if '_continue' in request.POST:
        # Try to find next task available for the user
        task_class = process.flow_class.task_class

        user_tasks = task_class._default_manager \
            .filter(process=process, owner=request.user, status=activation.STATUS.ASSIGNED)

        if user_tasks.exists():
            task = user_tasks.first()
            return task.flow_task.get_task_url(task, url_type='guess', user=request.user, namespace=namespace)
        else:
            user_tasks = task_class._default_manager.user_queue(request.user)\
                .filter(process=process, status=activation.STATUS.NEW)
            if user_tasks.exists():
                task = user_tasks.first()
                return task.flow_task.get_task_url(task, url_type='guess', user=request.user, namespace=namespace)

    elif 'back' in request.GET:
        # Back to task list
        back_url = request.GET['back']
        if not is_safe_url(url=back_url, allowed_hosts={request.get_host()}):
            back_url = '/'
        return back_url

    # Back to process list
    if process and process.pk:
        return reverse('{}:detail'.format(namespace),
                       kwargs={'process_pk': process.pk})
    else:
        return reverse('{}:index'.format(namespace))
