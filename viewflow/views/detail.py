# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from django.contrib.admin.utils import unquote
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views import generic

from viewflow.utils import has_object_perm, get_object_data


@method_decorator(login_required, name="dispatch")
class DetailModelView(generic.DetailView):
    viewset = None
    page_actions = None
    object_actions = None

    def has_view_permission(self, user, obj=None):
        if self.viewset is not None and hasattr(self.viewset, "has_view_permission"):
            return self.viewset.has_view_permission(user, obj=obj)
        else:
            return has_object_perm(
                user, "view", self.model, obj=obj
            ) or has_object_perm(user, "change", self.model, obj=obj)

    def get_object_data(self):
        """List of object fields to display.
        Choice fields values are expanded to readable choice label.
        """
        return get_object_data(self.object)

    def get_page_actions(self, *actions):
        if self.viewset:
            actions = (
                self.viewset.get_detail_page_actions(self.request, self.object)
                + actions
            )
        if self.page_actions:
            actions = self.page_actions + actions
        return actions

    def get_object_actions(self, *actions):
        if self.viewset:
            actions = (
                self.viewset.get_detail_page_object_actions(self.request, self.object)
                + actions
            )
        if self.object_actions:
            actions = self.object_actions + actions
        return actions

    def get_object_change_link(self):
        from viewflow.urls import current_viewset_reverse

        if self.viewset and hasattr(self.viewset, "has_change_permission"):
            if self.viewset.has_change_permission(self.request.user, self.object):
                return current_viewset_reverse(
                    self.request, self.viewset, "change", kwargs={"pk": self.object.pk}
                )

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        if pk is not None:
            pk = unquote(pk)
            try:
                self.kwargs[self.pk_url_kwarg] = self.model._meta.pk.to_python(pk)
            except (ValidationError, ValueError):
                raise Http404
        obj = super().get_object()

        if not self.has_view_permission(self.request.user, obj):
            raise PermissionDenied

        return obj

    def get_template_names(self):
        """
        List of templates for the view.
        If no `self.template_name` defined, uses::
             [<app_label>/<model_label>_detail.html,
              'viewflow/views/confirm_delete.html']
        """
        if self.template_name is None:
            opts = self.model._meta
            return [
                "{}/{}{}.html".format(
                    opts.app_label, opts.model_name, self.template_name_suffix
                ),
                "viewflow/views/detail.html",
            ]
        return [self.template_name]
