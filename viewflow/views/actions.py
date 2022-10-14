# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from django.db import router
from django.db.models.deletion import Collector
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.views import generic
from django.views.generic.list import MultipleObjectMixin
from .base import BulkActionForm
from .list import FilterableViewMixin


class BaseBulkActionView(FilterableViewMixin, MultipleObjectMixin, generic.FormView):
    model = None
    viewset = None

    form_class = BulkActionForm
    template_name_suffix = '_action'

    def get_template_names(self):
        opts = self.model._meta
        return [
            '{}/{}{}.html'.format(
                opts.app_label,
                opts.model_name,
                self.template_name_suffix),
            self.template_name,
        ]

    def get_success_url(self):
        if self.viewset and hasattr(self.viewset, 'get_success_url'):
            return self.viewset.get_success_url(self.request)
        return '../'

    def get_form_kwargs(self):
        return {
            'model': self.model,
            **super().get_form_kwargs(),
        }

    def get_queryset(self):
        queryset = super().get_queryset()
        pks = self.request.POST.getlist('pk')
        select_all = self.request.POST.get('select_all')
        if not select_all and pks:
            queryset = queryset.filter(pk__in=pks)
        self.object_list = queryset
        return queryset

    @cached_property
    def objects_count(self):
        if self.request.POST.get('select_all') and not self.filterset.form.has_changed():
            return None
        return self.object_list.count()

    def form_not_confirmed(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        messages.add_message(self.request, messages.SUCCESS, 'No objects selected', fail_silently=True)
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.form = self.get_form()
        self.object_list = self.get_queryset()
        if self.form.is_valid():
            if '_confirm' in self.request.POST:
                return self.form_valid(self.form)
            else:
                return self.form_not_confirmed(self.form)
        else:
            return self.form_invalid(self.form)


class DeleteBulkActionView(BaseBulkActionView):
    template_name = 'viewflow/views/delete_action.html'
    template_name_suffix = '_delete_action'

    def get_deleted_objects(self, query):
        collector = Collector(using=router.db_for_write(self.model))
        collector.collect(query)
        return [
            (model_class, objects)
            for model_class, objects in collector.data.items()
        ]

    def get_context_data(self, **kwargs):
        """Extend view context data.
        `{{ deleted_objects }}` - list of related objects to delete
        """
        if self.form.is_valid() and not self.form.cleaned_data.get('select_all'):
            kwargs.setdefault('deleted_objects', self.get_deleted_objects(self.get_queryset()))
        return super(DeleteBulkActionView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self.get_queryset().delete()
        self.message_user()
        return HttpResponseRedirect(self.get_success_url())

    def message_user(self):
        message = "The objects was deleted successfully"
        messages.add_message(self.request, messages.SUCCESS, message, fail_silently=True)
