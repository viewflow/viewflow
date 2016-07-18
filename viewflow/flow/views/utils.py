from collections import OrderedDict

from django.core.urlresolvers import reverse
from django.utils.http import is_safe_url

from ... import activation


def flow_start_actions(flow_cls, namespace, user=None):
    """Return list of start flow actions data available."""
    from ... import flow

    actions = []
    for node in flow_cls._meta.nodes():
        if isinstance(node, flow.Start) and (user is None or node.can_execute(user)):
            node_url = reverse('{}:{}'.format(namespace, node.name))
            actions.append((node_url, node.name))

    actions.sort(key=lambda action: action[0])
    return actions


def flows_start_actions(flow_classes, user=None):
    actions = OrderedDict()

    for namespace, flow_cls in sorted(flow_classes.items(), key=lambda item: item[1].process_title):
        actions[flow_cls] = flow_start_actions(flow_cls, namespace, user=user)
    return actions


def get_next_task_url(request, process):
    """Heuristic for user on complete task redirect."""
    namespace = request.resolver_match.namespace

    if '_continue' in request.POST:
        # Try to find next task available for the user
        task_cls = process.flow_cls.task_cls

        user_tasks = task_cls._default_manager \
            .filter(process=process, owner=request.user, status=activation.STATUS.ASSIGNED)

        if user_tasks.exists():
            task = user_tasks.first()
            return task.flow_task.get_task_url(task, url_type='guess', user=request.user, namespace=namespace)
        else:
            user_tasks = task_cls._default_manager.user_queue(request.user)\
                .filter(process=process, status=activation.STATUS.NEW)
            if user_tasks.exists():
                task = user_tasks.first()
                return task.flow_task.get_task_url(task, url_type='guess', user=request.user, namespace=namespace)

    elif 'back' in request.GET:
        # Back to task list
        back_url = request.GET['back']
        if not is_safe_url(url=back_url, host=request.get_host()):
            back_url = '/'
        return back_url

    # Back to process list
    if process and process.pk:
        return reverse('{}:detail'.format(namespace),
                       kwargs={'process_pk': process.pk})
    else:
        return reverse('{}:index'.format(namespace))
