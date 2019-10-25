from django.apps import AppConfig
from django.template import Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.utils.module_loading import autodiscover_modules
from django.utils.module_loading import import_string

from material import frontend
from material.frontend.apps import ModuleMixin

from ..compat import _


class ViewflowFrontendConfig(ModuleMixin, AppConfig):
    """Application config for the viewflow frontend."""

    name = 'viewflow.frontend'
    label = 'viewflow_frontend'
    verbose_name = _("Workflow")
    icon = '<i class="material-icons">assignment</i>'
    viewset = 'viewflow.frontend.viewset.FrontendViewSet'

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
        return user.is_authenticated

    def ready(self):
        """Import all <app>/flows.py modules."""
        autodiscover_modules('flows', register_to=self)
        viewset_class = import_string(self.viewset)
        self.viewset = viewset_class(self._registry)

    @property
    def urls(self):  # noqa D102
        base_url = '^workflow/'

        return frontend.ModuleURLResolver(
            base_url, self.viewset.urls, module=self)

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
        return self.viewset.ns_map

    @property
    def flows(self):
        """List of all registered flows."""
        return self._registry.keys()

    @property
    def sites(self):
        """List of all flows with a title."""
        return sorted(
            [
                (flow_class.process_title, flow_class)
                for flow_class in self._registry.keys()
            ], key=lambda item: item[0])
