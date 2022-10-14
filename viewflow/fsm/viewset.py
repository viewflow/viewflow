# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is licensed under the Commercial license defined in file
# 'COMM_LICENSE', which is part of this source code package.

from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.translation import gettext_lazy as _
from viewflow.urls import ViewsetMeta
from viewflow.views import Action, UpdateModelView
from viewflow.utils import viewprop, get_object_data

from viewflow.forms import ModelForm


from .base import State, TransitionBoundMethod


class ModelTransitionView(UpdateModelView):
    template_name_suffix = "_transition"

    def get_transition_fields(self, request, obj, slug):
        return self.viewset.get_transition_fields(request, obj, slug)

    def get_object_data(self):
        """List of object fields to display.
        Choice fields values are expanded to readable choice label.
        """
        return get_object_data(self.object)

    def get_template_names(self):
        """
        List of templates for the view.
        If no `self.template_name` defined, uses::
             [<app_label>/<model_label>_<suffix>.html,
              <app_label>/<model_label>_transition.html,
              'viewflow/views/transition.html']
        """
        if self.template_name is None:
            opts = self.model._meta
            return [
                "{}/{}{}.html".format(
                    opts.app_label, opts.model_name, self.template_name_suffix
                ),
                "{}/{}_transition.html".format(opts.app_label, opts.model_name),
                "viewflow/views/transition.html",
            ]
        return [self.template_name]

    def get_form_class(self):
        if self.form_class is None:
            return modelform_factory(
                self.model,
                form=ModelForm,
                fields=self.get_transition_fields(
                    self.request, self.object, self.kwargs["slug"]
                ),
            )
        else:
            return super().get_form_class()

    def form_valid(self, form):
        self.object = form.save()
        self.transition()
        return HttpResponseRedirect(self.get_success_url())

    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)

        flow = self.viewset.get_object_flow(self.request, obj)
        slug = self.kwargs["slug"]
        self.transition = (
            getattr(flow, slug, None) if not slug.startswith("_") else None
        )
        if not self.transition or not isinstance(
            self.transition, TransitionBoundMethod
        ):
            raise SuspiciousOperation

        if not self.transition.has_perm(self.request.user):
            raise PermissionDenied

        if not self.transition.can_proceed():
            raise PermissionDenied(_("Transition is not allowed"))

        return obj


class FlowViewsMixin(metaclass=ViewsetMeta):
    flow_state = None
    transition_view_class = ModelTransitionView

    def get_flow_state(self, request) -> State:
        if self.flow_state is None:
            raise ValueError("flow_state attribute is not defined.")
        return self.flow_state

    def get_object_flow(self, request, obj):
        try:
            return self.get_flow_state()._owner(obj)
        except TypeError:
            raise ValueError(
                "%s has no constructor with single argument. Please "
                "redefine .get_object_flow(self, request, obj) on the "
                "viewset" % self.flow_state._owner
            )

    def get_transition_fields(self, request, obj, slug):
        return []

    def get_detail_page_object_actions(self, request, obj, *actions):
        state = self.get_flow_state(request)
        flow = self.get_object_flow(request, obj)
        transitions = [
            (
                transition,
                transition.conditions_met(flow),
                transition.has_perm(flow, request.user),
            )
            for transition in state.get_outgoing_transitions(state.get(flow))
        ]

        additional_actions = [
            Action(
                name=transition.label,
                url=self.reverse("transition", args=[obj.pk, transition.slug]),
            )
            for transition, conditions_met, has_perm in transitions
            if conditions_met and has_perm
        ]

        if actions:
            additional_actions = (*additional_actions, *actions)

        return super().get_detail_page_object_actions(request, obj, *additional_actions)

    """
    Default transition view
    """

    def get_transition_view_kwargs(self, **kwargs):
        view_kwargs = {**self.transition_view_kwargs, **kwargs}
        return self.filter_kwargs(self.transition_view_class, **view_kwargs)

    @viewprop
    def transition_view_kwargs(self):
        return {}

    @viewprop
    def transition_view(self):
        return self.transition_view_class.as_view(**self.get_transition_view_kwargs())

    def _get_urls(self):
        urlpatterns = super()._get_urls()
        urlpatterns.append(
            path(
                "<path:pk>/transition/<slug:slug>/",
                self.transition_view,
                name="transition",
            )
        )
        return urlpatterns
