from django.core.paginator import Paginator, InvalidPage, EmptyPage


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
