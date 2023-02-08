from django.urls import path
from django.utils.functional import cached_property
from viewflow.urls import AppMenuMixin, Viewset
from viewflow.utils import viewprop, DEFAULT

from dash import Dash

from . import views


class Dashboard(AppMenuMixin, Viewset):
    layout = None
    dashboard_template_name = DEFAULT
    turbo_disabled = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registered_callbacks = []

    @cached_property
    def dash_app(self):
        app = Dash("app", requests_pathname_prefix=self.reverse("index"))
        app.layout = self.layout
        for func, args, kwargs in self._registered_callbacks:
            app.callback(*args, **kwargs)(func)
        return app

    def filter_kwargs(self, view_class, **kwargs):
        return super().filter_kwargs(view_class, **{"viewset": self, **kwargs})

    """
    Dashboard View
    """
    dashboard_view_class = views.DashboardView

    @property
    def index_path(self):
        return path("", self.dashboard_view, name="index")

    @viewprop
    def dashboard_view_kwargs(self):
        return {}

    def get_dashboard_view_kwargs(self, **kwargs):
        view_kwargs = {
            "template_name": self.dashboard_template_name,
            **self.dashboard_view_kwargs,
            **kwargs,
        }
        return self.filter_kwargs(self.dashboard_view_class, **view_kwargs)

    @viewprop
    def dashboard_view(self):
        return self.dashboard_view_class.as_view(**self.get_dashboard_view_kwargs())

    """
    Dash endpoints
    """

    @property
    def layout_path(self):
        return path("_dash-layout/", views.layout_endpoint, {"viewset": self})

    @property
    def dependencies_path(self):
        return path(
            "_dash-dependencies/", views.dependencies_endpoint, {"viewset": self}
        )

    @property
    def update_component_path(self):
        return path(
            "_dash-update-component", views.update_component_endpoint, {"viewset": self}
        )

    """
    Callback
    """

    def callback(self, *args, **kwargs):
        def decorator(func):
            self._registered_callbacks.append((func, args, kwargs))
            return func

        return decorator
