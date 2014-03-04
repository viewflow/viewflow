from django.core import urlresolvers
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import redirect as django_redirect


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


def redirect(to, permanent=False, current_app=None, *args, **kwargs):
    """
    redirect that takes into account current_app parameter for url resolution
    """
    if current_app:
        try:
            to = urlresolvers.reverse(to, args=args, kwargs=kwargs)
        except urlresolvers.NoReverseMatch:
            pass

    return django_redirect(to, permanent=permanent, *args, **kwargs)
