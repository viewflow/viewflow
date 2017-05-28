from django.conf.urls import url, include

from .views import (
    CancelProcessView, DetailProcessView, ProcessListView,
    QueueListView, ArchiveListView, TaskListView
)


class FlowViewSet(object):
    """
    Shortcut for a flow urls routing.

    Usage::

        urlpatterns = [
            url(r'/helloworld/', include(FlowViewSet(HelloWorldFlow).urls))
        ]
    """

    process_list_view = [
        r'^$',
        ProcessListView.as_view(),
        'index'
    ]

    detail_process_view = [
        r'^(?P<process_pk>\d+)/$',
        DetailProcessView.as_view(),
        'detail'
    ]

    cancel_process_view = [
        r'^action/cancel/(?P<process_pk>\d+)/$',
        CancelProcessView.as_view(),
        'action_cancel'
    ]

    queue_list_view = [
        '^queue/$',
        QueueListView.as_view(),
        'queue',
    ]

    archive_list_view = [
        '^archive/$',
        ArchiveListView.as_view(),
        'archive',
    ]

    inbox_list_view = [
        '^tasks/$',
        TaskListView.as_view(),
        'tasks'
    ]

    def __init__(self, flow_class):  # noqa D102
        self.flow_class = flow_class

    def _create_url_entry(self, url_entry):
        regexp, view, name = url_entry
        return url(regexp, view, name=name)

    def get_list_urls(self):
        """Collect urls from viewset class."""
        attrs = (getattr(self, attr) for attr in dir(self) if attr.endswith('_view'))
        return [
            self._create_url_entry(value)
            for value in attrs if isinstance(value, (list, tuple))
        ]

    @property
    def urls(self):
        """Collect the viewset and flow urls."""
        return [
            url('', include(self.get_list_urls()), {'flow_class': self.flow_class}),
            self.flow_class.instance.urls
        ]
