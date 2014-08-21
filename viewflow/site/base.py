from django.conf.urls import patterns, url, include
from django.core.urlresolvers import reverse

from . import views
from .sidebar import SideItem


class FlowSideItem(SideItem):
    def __init__(self, *args, **kwargs):
        self.flow_cls = kwargs.pop('flow_cls')
        super(FlowSideItem, self).__init__(*args, **kwargs)

    def can_view(self, user):
        return self.flow_cls.can_view(user)


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
        home = FlowSideItem(self.flow_cls.process_title,
                            reverse('viewflow:index', current_app=self.flow_cls._meta.namespace),
                            flow_cls=self)
        yield home
        yield SideItem('Tasks', reverse('viewflow:tasks', current_app=self.flow_cls._meta.namespace), parent=home)
        yield SideItem('Queue', reverse('viewflow:queue', current_app=self.flow_cls._meta.namespace), parent=home)

    def can_view(self, user):
        opts = self.flow_cls.process_cls._meta
        view_perm = "{}.view_{}".format(opts.app_label, opts.model_name)
        return user.has_perm(view_perm)


class ViewSite(object):
    login_view = views.LoginView
    logout_view = views.LogoutView

    # all process views
    process_list_view = views.AllProcessListView
    tasks_view = views.AllTaskListView
    queue_view = views.AllQueueListView

    def __init__(self, app_name='viewsite_default'):
        self._registry = {}

        self.app_name = app_name
        self.flow_sites = {}

    @property
    def sites(self):
        if not self.flow_sites:
            for flow_cls, flow_site in self._registry.items():
                site = flow_site(view_site=self, flow_cls=flow_cls)
                self.flow_sites[flow_cls] = site
        return self.flow_sites.items()

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

        for flow_cls, flow_site in self.sites:
            result += flow_site.urls

        return result

    def sideitems(self):
        home = SideItem('Home', reverse('viewflow_site:index', current_app=self.app_name))
        yield home
        yield SideItem('Tasks', reverse('viewflow_site:tasks', current_app=self.app_name), parent=home)
        yield SideItem('Queue', reverse('viewflow_site:queue', current_app=self.app_name), parent=home)

        for flow_cls, flow_site in sorted(self.sites, key=lambda data: data[0].process_title):
            for item in flow_site.sideitems():
                yield item

    def register(self, flow_cls, flow_site=None):
        if flow_cls not in self._registry:
            if flow_site is None:
                flow_site = FlowSite

            self._registry[flow_cls] = flow_site
