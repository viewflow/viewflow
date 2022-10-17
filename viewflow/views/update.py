# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.
from urllib.parse import quote as urlquote

from django.contrib import messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms.models import modelform_factory
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views import generic

from viewflow.forms import FormAjaxCompleteMixin, FormDependentSelectMixin, ModelForm
from viewflow.utils import has_object_perm, viewprop

from .base import FormLayoutMixin


@method_decorator(login_required, name='dispatch')
class UpdateModelView(FormLayoutMixin, FormDependentSelectMixin, FormAjaxCompleteMixin, generic.UpdateView):
    viewset = None
    layout = None
    form_widgets = None
    page_actions = None

    def has_change_permission(self, request, obj=None):
        if self.viewset is not None and hasattr(self.viewset, "has_change_permission"):
            return self.viewset.has_change_permission(request.user, obj=obj)
        else:
            return has_object_perm(request.user, "change", self.model, obj=obj)

    def get_object_url(self, obj):
        if self.viewset is not None and hasattr(self.viewset, "get_object_url"):
            return self.viewset.get_object_url(self.request, obj)
        elif hasattr(obj, "get_absolute_url"):
            if self.has_change_permission(self.request, obj):
                return obj.get_absolute_url()

    def get_page_actions(self, *actions):
        if self.viewset and hasattr(self.viewset, "get_update_page_actions"):
            actions = (
                self.viewset.get_update_page_actions(self.request, self.object)
                + actions
            )
        if self.page_actions:
            actions = self.page_actions + actions
        return actions

    def message_user(self):
        url = self.get_object_url(self.object)
        link = ""
        if url:
            link = format_html('<a href="{}">{}</a>', urlquote(url), _("View"))

        message = format_html(
            _("The {obj} was changed successfully. {link}"),
            obj=str(self.object),
            link=link,
        )
        messages.add_message(
            self.request, messages.SUCCESS, message, fail_silently=True
        )

    @viewprop
    def queryset(self):
        if self.viewset is not None and hasattr(self.viewset, "get_queryset"):
            return self.viewset.get_queryset(self.request)
        return None

    def get_form_class(self):
        if self.form_class is None:
            return modelform_factory(
                self.model,
                form=ModelForm,
                fields=self.fields,
                widgets=self.form_widgets,
            )
        return self.form_class

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            pk = unquote(pk)
            try:
                self.kwargs[self.pk_url_kwarg] = self.model._meta.pk.to_python(pk)
            except (ValidationError, ValueError):
                raise Http404
        obj = super().get_object()

        if not self.has_change_permission(self.request, obj):
            raise PermissionDenied

        return obj

    def get_template_names(self):
        """
        List of templates for the view.
        If no `self.template_name` defined, uses::
             [<app_label>/<model_label>_<suffix>.html,
              <app_label>/<model_label>_form.html,
              'viewflow/views/form.html']
        """
        if self.template_name is None:
            opts = self.model._meta
            return [
                "{}/{}{}.html".format(
                    opts.app_label, opts.model_name, self.template_name_suffix
                ),
                "{}/{}_form.html".format(opts.app_label, opts.model_name),
                "viewflow/views/form.html",
            ]
        return [self.template_name]

    def form_valid(self, *args, **kwargs):
        response = super(UpdateModelView, self).form_valid(*args, **kwargs)
        self.message_user()
        return response

    def get_success_url(self):
        if self.viewset and hasattr(self.viewset, "get_success_url"):
            return self.viewset.get_success_url(self.request, obj=self.object)
        return "../"
