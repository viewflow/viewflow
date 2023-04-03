# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is licensed under the Commercial license defined in file
# 'COMM_LICENSE', which is part of this source code package.

from contextlib import contextmanager
from functools import partial

from django.conf import settings
from django.contrib.admin import helpers
from django.contrib.admin.utils import flatten_fieldsets, quote
from django.contrib.admin.exceptions import DisallowedModelAdminLookup
from django.core.exceptions import PermissionDenied
from django.forms import Media
from django.forms.models import modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

from viewflow import fsm
from viewflow.fsm.base import State, TransitionBoundMethod


class FlowAdminMixin(object):
    """
    A Mixin for providing Finite State Machine (FSM) management support in
    Django admin.

    """

    flow_state: State

    change_list_template = "admin/fsm_change_list.html"
    change_form_template = "admin/fsm_change_form.html"

    transition_form_template = None

    def get_flow_state(self, request) -> State:
        return self.flow_state

    def get_object_flow(self, request, obj):
        """
        Returns the flow object associated with the specified model object.

        This function retrieves the flow object associated with the given model
        object. Override this function if your flow class does not have a
        constructor that accepts the model object as the only argument.
        """
        try:
            return self.get_flow_state()._owner(obj)
        except TypeError:
            raise ValueError(
                f"{self.flow_state._owner} does not have a constructor that accepts"
                " a single argument. Please redefine 'get_object_flow' on the model"
                " admin."
            )

    def get_transition_fields(self, request, obj, slug):
        """
        Override this method to return a list of editable fields for the form
        associated with the specified transition slug.

        If no fields are editable for the transition, this function should return
        None.
        """
        return None

    def save_model(self, request, obj, form, change):
        if not change:
            state = self.get_flow_state(request)
            flow = self.get_object_flow(request, obj)
            state.set(flow, state.get(flow))
        super().save_model(request, obj, form, change)

    @contextmanager
    def create_revision(self, request):
        """
        Save wrapper to use in state transition views, in case of subclass of
        django-reversion VersionAdmin.
        """
        if hasattr(super(), "create_revision"):
            with super().create_revision(request):
                yield
        else:
            yield

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "<path:object_id>/transition/<slug:slug>/",
                self.admin_site.admin_view(self.transition_view),
                name="%s_%s_transition" % info,
            ),
        ] + super().get_urls()

    @property
    def media(self):
        extra = ".min"  # '' if settings.DEBUG else '.min'

        return super().media + Media(
            css={
                "screen": (
                    "viewflow/css/vis-network%s.css" % extra,
                    "viewflow/css/viewflow%s.css" % extra,
                )
            },
            js=[
                "viewflow/js/vis-network%s.js" % extra,
                "viewflow/js/viewflow%s.js" % extra,
            ],
        )

    def changelist_view(self, request, extra_context=None):
        state = self.get_flow_state(request)
        flow_chart = fsm.chart(state)

        return super().changelist_view(
            request, extra_context={"state": state, "flow_chart": flow_chart}
        )

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        if change:
            state = self.get_flow_state(request)
            flow = self.get_object_flow(request, obj)

            context.update(
                {
                    "state": state,
                    "flow": flow,
                    "transitions": [
                        (
                            transition,
                            transition.conditions_met(flow),
                            transition.has_perm(flow, request.user),
                        )
                        for transition in state.get_outgoing_transitions(
                            state.get(flow)
                        )
                    ],
                }
            )

        return super().render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj
        )

    def transition_view(self, request, object_id, slug):
        opts = self.model._meta
        obj = self.get_object(request, object_id)
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, opts, object_id)

        flow = self.get_object_flow(request, obj)
        transition = getattr(flow, slug, None) if not slug.startswith("_") else None
        if not transition or not isinstance(transition, TransitionBoundMethod):
            raise DisallowedModelAdminLookup

        if not transition.has_perm(request.user):
            raise PermissionDenied

        if not transition.can_proceed():
            raise PermissionDenied(_("Transition is not allowed"))

        # build form
        fields = self.get_transition_fields(request, obj, slug) or []
        readonly_fields = [
            field
            for field in flatten_fieldsets(self.get_fieldsets(request, obj))
            if field not in fields
        ]

        ModelForm = modelform_factory(
            self.model,
            **{
                "form": self.form,
                "fields": fields,
                "formfield_callback": partial(
                    self.formfield_for_dbfield, request=request
                ),
            },
        )
        form = ModelForm(request.POST or None, instance=obj)
        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request, obj)),
            {},
            readonly_fields,
            model_admin=self,
        )
        media = self.media + adminForm.media

        if form.is_valid():
            # perform transition
            self.save_model(request, obj, form, change=True)
            transition()

            obj_url = reverse(
                "admin:%s_%s_change" % (opts.app_label, opts.model_name),
                args=(quote(obj.pk),),
                current_app=self.admin_site.name,
            )

            return HttpResponseRedirect(obj_url)

        context = {
            **self.admin_site.each_context(request),
            "title": _("%(label)s %(name)s")
            % ({"label": transition.label, "name": opts.verbose_name}),
            "adminform": adminForm,
            "object_id": object_id,
            "original": obj,
            "media": media,
            "preserved_filters": self.get_preserved_filters(request),
            "transition": transition,
            "opts": opts,
            "has_view_permission": self.has_view_permission(request, obj),
        }

        return render(
            request,
            self.transition_form_template
            or [
                "admin/%s/%s/fsm_transition_form.html"
                % (opts.app_label, opts.model_name),
                "admin/%s/fsm_transition_form.html" % opts.app_label,
                "admin/fsm_transition_form.html",
            ],
            context,
        )
