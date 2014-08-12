from django.core.urlresolvers import reverse


def get_next_task_url(process, user, default='viewflow:index'):
    """
    Checks is there any active task that user owns, if so
    redirects to it, else, return viewflow:index
    """
    task_cls = process.flow_cls.task_cls

    user_tasks = task_cls._default_manager \
        .filter(process=process, owner=user, status=task_cls.STATUS.ASSIGNED)

    if user_tasks.exists():
        return user_tasks.first().get_absolute_url()
    elif '/' in default:
        return default
    else:
        return reverse(default, current_app=process.flow_cls._meta.namespace)
