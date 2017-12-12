import itertools
from django.conf.urls import url, include

from ..flow.viewset import FlowViewSet as BaseFlowViewSet
from . import views


class FlowViewSet(BaseFlowViewSet):
    process_list_view = [
        r'^$',
        views.ProcessListView.as_view(),
        'index'
    ]


class FrontendViewSet(object):
    def __init__(self, registry):
        self.registry = registry

    @property
    def ns_map(self):
        return {
            flow_class: "{}:{}".format(
                flow_class._meta.app_label,
                flow_class._meta.flow_label)
            for flow_class, flow_site in self.registry.items()
        }

    def filter_kwargs(self, view_class, **kwargs):
        """Add defaults and filter kwargs to only thouse that view can accept.

        Viewset pass to the view only kwargs that have non DEFAULT values,
        and if the view have a corresponding attribute.

        In addition, if view has `viewset` attribute, it will receive
        the `self` instance

        """
        result = {
            'ns_map': self.ns_map,
            'viewset': self,
        }
        result.update(kwargs)
        return {name: value for name, value in result.items()
                if hasattr(view_class, name)}

    """
    Inbox
    """
    inbox_view_class = views.AllTaskListView

    def get_inbox_view(self):
        return self.inbox_view_class.as_view(**self.get_inbox_view_kwargs())

    def get_inbox_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.inbox_view_class, **kwargs)

    @property
    def inbox_view(self):
        return [
            '^$',
            self.get_inbox_view(),
            'index'
        ]

    """
    Queue
    """
    queue_view_class = views.AllQueueListView

    def get_queue_view(self):
        return self.queue_view_class.as_view(**self.get_queue_view_kwargs())

    def get_queue_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.queue_view_class, **kwargs)

    @property
    def queue_view(self):
        return [
            '^queue/$',
            self.get_queue_view(),
            "queue"
        ]

    """
    Archive
    """
    archive_view_class = views.AllArchiveListView

    def get_archive_view(self):
        return self.archive_view_class.as_view(**self.get_archive_view_kwargs())

    def get_archive_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.archive_view_class, **kwargs)

    @property
    def archive_view(self):
        return [
            '^archive/$',
            self.get_archive_view(),
            "archive"
        ]

    """
    Tasks Action: Assign
    """
    tasks_assign_view_class = views.TasksAssignView

    def get_tasks_assign_view(self):
        return self.tasks_assign_view_class.as_view(
            **self.get_tasks_assign_view_kwargs())

    def get_tasks_assign_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.tasks_assign_view_class, **kwargs)

    @property
    def tasks_assign_view(self):
        return [
            '^action/assign/$',
            self.get_tasks_assign_view(),
            'assign'
        ]

    """
    Tasks Action: Deassign
    """
    tasks_unassign_view_class = views.TasksUnAssignView

    def get_tasks_unassign_view(self):
        return self.tasks_unassign_view_class.as_view(
            **self.get_tasks_unassign_view_kwargs())

    def get_tasks_unassign_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.tasks_unassign_view_class, **kwargs)

    @property
    def tasks_unassign_view(self):
        return [
            '^action/unassign/$',
            self.get_tasks_unassign_view(),
            'unassign'
        ]

    def collect_flows_urls(self):
        result = []

        items = sorted(self.registry.items(), key=lambda item: item[0]._meta.app_label)
        app_flows = itertools.groupby(
            items, lambda item: item[0]._meta.app_label)

        for app_label, items in app_flows:
            app_views = []
            for flow_class, flow_router in items:
                flow_label = flow_class._meta.flow_label
                app_views.append(
                    url('^{}/'.format(flow_label), include((flow_router.urls, flow_label)))
                )

            result.append(
                url('^{}/'.format(app_label), include((app_views, app_label)))
            )

        return result

    def collect_viewset_urls(self):
        result = []

        url_entries = (
            getattr(self, attr)
            for attr in dir(self)
            if attr.endswith('_view')
            if isinstance(getattr(self, attr), (list, tuple))
        )

        for url_entry in url_entries:
            url_re, view, name = url_entry
            result.append(url(url_re, view, name=name))

        return result

    @property
    def urls(self):
        viewset_urls = self.collect_viewset_urls()
        flow_urls = self.collect_flows_urls()

        return [
            url('^', (viewset_urls + flow_urls, 'viewflow', 'viewflow'))
        ]
