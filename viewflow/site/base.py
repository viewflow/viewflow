from django.conf.urls import patterns, url, include

from . import views


class FlowSite(object):
    process_list_view = staticmethod(views.ProcessListView.as_view())
    process_detail_view = staticmethod(views.ProcessDetailView.as_view())
    task_list_view = staticmethod(views.TaskListView.as_view())
    queue_view = staticmethod(views.QueueListView.as_view())

    def __init__(self, view_site, flow_cls):
        self.view_site = view_site
        self.flow_cls = flow_cls

    @property
    def urls(self):
        flow_patterns, namespace, app_name = self.flow_cls.instance.urls

        list_patterns = patterns(
            '',
            url('^$', self.process_list_view,
                {'flow_site': self, 'flow_cls': self.flow_cls}, name='index'),
            url('^(?P<process_pk>\d+)/$', self.process_detail_view,
                {'flow_site': self, 'flow_cls': self.flow_cls}, name='details'),
            url('^tasks/$', self.task_list_view,
                {'flow_site': self, 'flow_cls': self.flow_cls}, name='tasks'),
            url('^queue/$', self.queue_view,
                {'flow_site': self, 'flow_cls': self.flow_cls}, name='queue')
        )

        return patterns(
            '',
            url('^{}/'.format(self.flow_cls._meta.flow_label),
                include(list_patterns + flow_patterns, app_name, namespace)))


class ViewSite(object):
    login_view = staticmethod(views.LoginView.as_view())
    logout_view = staticmethod(views.LogoutView.as_view())

    # all process views
    processes_list_view = staticmethod(views.AllProcessListView.as_view())
    tasks_list_view = staticmethod(views.AllTaskListView.as_view())
    queues_view = staticmethod(views.AllQueueListView.as_view())

    def __init__(self, app_name='viewsite_default'):
        self.app_name = app_name
        self.flow_sites = {}

    @property
    def urls(self):
        site_patterns = patterns(
            '',
            url('^$', self.processes_list_view, {'view_site': self}, name="index"),
            url('^login/$', self.login_view, {'view_site': self}, name="login"),
            url('^logout/$', self.logout_view, {'view_site': self}, name="logout"),
            url('^tasks/$', self.tasks_list_view, {'view_site': self}, name="tasks"),
            url('^queue/$', self.queues_view, {'view_site': self}, name="queues"),
        )

        result = patterns('', url('', include(site_patterns, self.app_name, 'viewflow_site')))

        for flow_cls, flow_site in self.flow_sites.items():
            site = flow_site(view_site=self, flow_cls=flow_cls)
            result += site.urls

        return result

    def register(self, flow_cls, flow_site=None):
        if flow_cls not in self.flow_sites:
            if flow_site is None:
                flow_site = FlowSite

            self.flow_sites[flow_cls] = flow_site
