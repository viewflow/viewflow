from django.conf.urls import patterns, url, include

from . import views


class ViewSite(object):
    login_view = staticmethod(views.LoginView.as_view())
    logout_view = staticmethod(views.LogoutView.as_view())

    # all process views
    processes_list_view = staticmethod(views.processes_list_view)
    tasks_list_view = staticmethod(views.tasks_list_view)
    queues_view = staticmethod(views.queues_view)

    # per-process views
    process_list_view = staticmethod(views.ProcessListView.as_view())
    process_detail_view = staticmethod(views.process_detail_view)
    task_list_view = staticmethod(views.task_list_view)
    queue_view = staticmethod(views.queue_view)

    def __init__(self, app_name='viewsite_default'):
        self.app_name = app_name
        self.flows = []

    @property
    def urls(self):
        site_patterns = patterns(
            '',
            url('^$', self.processes_list_view, {'flow_site': self}, name="index"),
            url('^login/$', self.login_view, {'flow_site': self}, name="login"),
            url('^logout/$', self.logout_view, {'flow_site': self}, name="logout"),
            url('^tasks/$', self.tasks_list_view, {'flow_site': self}, name="tasks"),
            url('^queues/$', self.queues_view, {'flow_site': self}, name="queues"),
        )

        urls = [
            url('', include(site_patterns, self.app_name, 'viewflow_site'))
        ]

        for flow_cls in self.flows:
            flow_patterns, namespace, app_name = flow_cls.instance.urls

            list_patterns = patterns(
                '',
                url('^$', self.process_list_view,
                    {'flow_site': self, 'flow_cls': flow_cls}, name='index'),
                url('^tasks/$', self.task_list_view,
                    {'flow_site': self, 'flow_cls': flow_cls}, name='tasks'),
                url('^queues/$', self.queue_view,
                    {'flow_site': self, 'flow_cls': flow_cls}, name='queue')
            )

            urls.append(
                url('^{}/'.format(flow_cls._meta.flow_label),
                    include(list_patterns + flow_patterns, app_name, namespace)))

        return patterns('', *urls)

    def register(self, flow_cls):
        if flow_cls not in self.flows:
            self.flows.append(flow_cls)
