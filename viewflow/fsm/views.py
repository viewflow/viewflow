# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is licensed under the Commercial license defined in file
# 'COMM_LICENSE', which is part of this source code package.

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views import generic

from viewflow.views.detail import DetailModelView
from viewflow.views.list import ListModelView

from .chart import chart


@method_decorator(login_required, name="dispatch")
class FSMChartView(generic.TemplateView):
    """Render the state machine diagram for a `FlowViewsMixin` viewset."""

    template_name = "viewflow/views/fsm_chart.html"
    viewset = None
    flow_state = None

    def get_flow_state(self):
        if self.viewset is not None:
            return self.viewset.get_flow_state(self.request)
        return self.flow_state

    def has_view_permission(self, user):
        if self.viewset is not None and hasattr(self.viewset, "has_view_permission"):
            return self.viewset.has_view_permission(user)
        return True

    def get(self, request, *args, **kwargs):
        if not self.has_view_permission(request.user):
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["flow_chart"] = chart(self.get_flow_state())
        return context


class FSMListModelView(ListModelView):
    """List view that shows the FSM flow chart alongside the object table."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.viewset is not None and hasattr(self.viewset, "get_flow_state"):
            context["flow_chart"] = chart(self.viewset.get_flow_state(self.request))
            context["flow_export_name"] = "%s-flow" % self.model._meta.model_name
        return context

    def get_template_names(self):
        if self.template_name is None:
            opts = self.model._meta
            return [
                "{}/{}{}.html".format(
                    opts.app_label, opts.model_name, self.template_name_suffix
                ),
                "viewflow/fsm/list.html",
                "viewflow/views/list.html",
            ]
        return [self.template_name]


class FSMDetailModelView(DetailModelView):
    """Detail view that includes the FSM flow chart in the context."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.viewset, "get_flow_state"):
            context["flow_chart"] = chart(self.viewset.get_flow_state(self.request))
        return context

    def get_template_names(self):
        if self.template_name is None:
            opts = self.model._meta
            return [
                "{}/{}{}.html".format(
                    opts.app_label, opts.model_name, self.template_name_suffix
                ),
                "viewflow/fsm/detail.html",
            ]
        return [self.template_name]
