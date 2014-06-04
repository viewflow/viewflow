from django.core.paginator import Paginator, InvalidPage, EmptyPage
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


def get_page(request, query, page_attr='page', per_page=25):
    """
    Paginate queryset, and returns requested int GET param page
    """
    paginator = Paginator(query, per_page)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get(page_attr, '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        result = paginator.page(page)
    except (EmptyPage, InvalidPage):
        result = paginator.page(paginator.num_pages)

    return result
