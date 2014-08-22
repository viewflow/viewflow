from django.core.urlresolvers import reverse
from django.utils.http import is_safe_url


def get_next_task_url(request, process):
    """
    Heruistic for user on complete task redirect
    """
    if '_continue' in request.POST:
        # Try to find next task available for the user
        task_cls = process.flow_cls.task_cls

        user_tasks = task_cls._default_manager \
            .filter(process=process, owner=request.user, status=task_cls.STATUS.ASSIGNED)

        if user_tasks.exists():
            return user_tasks.first().get_absolute_url()
        else:
            user_tasks = task_cls._default_manager.user_queue(request.user)\
                .filter(process=process, status=task_cls.STATUS.NEW)
            if user_tasks.exists():
                return user_tasks.first().get_absolute_url()

    elif 'back' in request.GET:
        # Back to task list
        back_url = request.GET['back']
        if not is_safe_url(url=back_url, host=request.get_host()):
            back_url = '/'
        return back_url

    # Back to process list
    if process and process.pk:
        return reverse('viewflow:details',
                       kwargs={'process_pk': process.pk},
                       current_app=process.flow_cls._meta.namespace)
    else:
        return reverse('viewflow:index', current_app=process.flow_cls._meta.namespace)
