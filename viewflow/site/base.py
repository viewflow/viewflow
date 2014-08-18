from django.conf.urls import patterns, url, include
from django.core.urlresolvers import reverse

from . import views
from .sidebar import SideItem


class FlowSite(object):
    process_list_view = views.ProcessListView
    process_detail_view = views.ProcessDetailView
    tasks_view = views.TaskListView
    queue_view = views.QueueListView

    def __init__(self, view_site, flow_cls):
        self.view_site = view_site
        self.flow_cls = flow_cls

    @property
    def urls(self):
        flow_patterns, namespace, app_name = self.flow_cls.instance.urls

        list_patterns = patterns(
            '',
            url('^$', self.process_list_view.as_view(flow_site=self), name='index'),
            url('^(?P<process_pk>\d+)/$', self.process_detail_view.as_view(flow_site=self), name='details'),
            url('^tasks/$', self.tasks_view.as_view(flow_site=self), name='tasks'),
            url('^queue/$', self.queue_view.as_view(flow_site=self), name='queue')
        )

        return patterns(
            '',
            url('^{}/'.format(self.flow_cls._meta.flow_label),
                include(list_patterns + flow_patterns, app_name, namespace)))

    def sideitems(self):
        home = SideItem(self.flow_cls.process_title,
                        reverse('viewflow:index', current_app=self.flow_cls._meta.namespace))
        yield home
        yield SideItem('Tasks', reverse('viewflow:tasks', current_app=self.flow_cls._meta.namespace), parent=home)
        yield SideItem('Queue', reverse('viewflow:queue', current_app=self.flow_cls._meta.namespace), parent=home)


class ViewSite(object):
    login_view = views.LoginView
    logout_view = views.LogoutView

    # all process views
    process_list_view = views.AllProcessListView
    tasks_view = views.AllTaskListView
    queue_view = views.AllQueueListView

    def __init__(self, app_name='viewsite_default'):
        self.app_name = app_name
        self.flow_sites_cls = {}
        self.flow_sites = {}

    @property
    def sites(self):
        if not self.flow_sites:
            for flow_cls, flow_site in self.flow_sites_cls.items():
                site = flow_site(view_site=self, flow_cls=flow_cls)
                self.flow_sites[flow_cls] = site
        return self.flow_sites

    @property
    def urls(self):
        site_patterns = patterns(
            '',
            url('^$', self.process_list_view.as_view(view_site=self), name="index"),
            url('^login/$', self.login_view.as_view(view_site=self), name="login"),
            url('^logout/$', self.logout_view.as_view(view_site=self), name="logout"),
            url('^tasks/$', self.tasks_view.as_view(view_site=self), name="tasks"),
            url('^queue/$', self.queue_view.as_view(view_site=self), name="queue"),
        )

        result = patterns('', url('', include(site_patterns, self.app_name, 'viewflow_site')))

        for flow_cls, flow_site in self.sites.items():
            result += flow_site.urls

        return result

    def sideitems(self):
        home = SideItem('Home', reverse('viewflow_site:index', current_app=self.app_name))
        yield home
        yield SideItem('Tasks', reverse('viewflow_site:tasks', current_app=self.app_name), parent=home)
        yield SideItem('Queue', reverse('viewflow_site:queue', current_app=self.app_name), parent=home)

        for flow_cls, flow_site in sorted(self.sites.items(), key=lambda data: data[0].process_title):
            for item in flow_site.sideitems():
                yield item

    def register(self, flow_cls, flow_site=None):
        if flow_cls not in self.flow_sites_cls:
            if flow_site is None:
                flow_site = FlowSite

            self.flow_sites_cls[flow_cls] = flow_site
