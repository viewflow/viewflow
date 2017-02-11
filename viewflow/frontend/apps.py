import itertools

from django.apps import AppConfig
from django.conf.urls import url, include
from django.core.urlresolvers import reverse
from django.template import Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.module_loading import autodiscover_modules

from material import frontend
from material.frontend.apps import ModuleMixin


class ViewflowFrontendConfig(ModuleMixin, AppConfig):
    """Application config for the viewflow fronend."""

    name = 'viewflow.frontend'
    label = 'viewflow_frontend'
    verbose_name = "Workflow"
    icon = '<i class="material-icons">assignment</i>'

    def __init__(self, app_name, app_module):  # noqa D102
        super(ViewflowFrontendConfig, self).__init__(app_name, app_module)
        self._registry = {}

    def register(self, flow_class, viewset_class=None):
        """Register a flow class at the frontend."""
        from .viewset import FlowViewSet

        if flow_class not in self._registry:
            if viewset_class is None:
                viewset_class = FlowViewSet

            self._registry[flow_class] = viewset_class(flow_class=flow_class)

    def has_perm(self, user):
        """Any authenticated user has a permission for the viewflow."""
        return user.is_authenticated()

    def ready(self):
        """Import all <app>/flows.py modules."""
        autodiscover_modules('flows', register_to=self)

    @property
    def urls(self):  # noqa D102
        from . import views
        from viewflow.frontend import views as frontend_views

        base_url = '^workflow/'

        module_views = [
            url('^$', frontend_views.AllTaskListView.as_view(ns_map=self.ns_map), name="index"),
            url('^queue/$', frontend_views.AllQueueListView.as_view(ns_map=self.ns_map), name="queue"),
            url('^archive/$', frontend_views.AllArchiveListView.as_view(ns_map=self.ns_map), name="archive"),
            url('^action/unassign/$', views.TasksUnAssignView.as_view(ns_map=self.ns_map), name="unassign"),
            url('^action/assign/$', views.TasksAssignView.as_view(ns_map=self.ns_map), name="assign"),
        ]

        app_flows = itertools.groupby(
            self._registry.items(),
            lambda item: item[0]._meta.app_label)
        for app_label, items in app_flows:
            app_views = []
            for flow_class, flow_router in items:
                flow_label = flow_class._meta.flow_label
                app_views.append(
                    url('^{}/'.format(flow_label), include(flow_router.urls, namespace=flow_label))
                )

            module_views.append(
                url('^{}/'.format(app_label), include(app_views, namespace=app_label))
            )

        patterns = [
            url('^', (module_views, 'viewflow', 'viewflow'))
        ]

        return frontend.ModuleURLResolver(
            base_url, patterns, module=self, app_name=self.label)

    def index_url(self):
        """Base view for the viewflow frontend."""
        return reverse('viewflow:index')

    def base_template(self):
        return get_template('viewflow/base_module.html')

    def menu(self):
        """Module menu."""
        try:
            return get_template('viewflow/menu.html')
        except TemplateDoesNotExist:
            return Template('')

    @property
    def ns_map(self):
        """Mapping flows to registred namespaces."""
        return {
            flow_class: "{}:{}".format(flow_class._meta.app_label, flow_class._meta.flow_label)
            for flow_class, flow_site in self._registry.items()
        }

    @property
    def flows(self):
        """List of all registred flows."""
        return self._registry.keys()

    @property
    def sites(self):
        """List of all flows with a title."""
        return sorted(
            [
                (flow_class.process_title, flow_class)
                for flow_class in self._registry.keys()
            ], key=lambda item: item[0])
