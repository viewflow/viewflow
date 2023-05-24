# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.
from urllib.parse import quote as urlquote

from django.contrib import messages
from django.utils.html import format_html
from django.urls.exceptions import NoReverseMatch


class SuccessMessageMixin(object):
    """Send a notification with link to the current process or task."""

    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message, fail_silently=True)
        return response

    def get_success_message(self, cleaned_data):
        activation = self.request.activation
        process, task = activation.process, activation.task

        try:
            process_url = process.flow_class.instance.reverse(
                "process_detail", args=[process.pk]
            )
            process_link = format_html(
                '<a href="{}">#{}</a>', urlquote(process_url), process.pk
            )
        except NoReverseMatch:
            process_link = f"#{process.pk}"

        task_url = task.flow_task.reverse("index", args=[process.pk, task.pk])
        task_link = format_html('<a href="{}">#{}</a>', urlquote(task_url), task.pk)

        return format_html(self.success_message, process=process_link, task=task_link)


class TaskSuccessUrlMixin(object):
    """Try to find .get_success_url method in the current application"""

    def get_success_url(self):
        """Continue on task or redirect back to task list."""
        if getattr(self, "success_url", None) is None:
            match = self.request.resolver_match
            if hasattr(match, "viewset") and hasattr(match.viewset, "get_success_url"):
                return match.viewset.get_success_url(self.request)

            activation = self.request.activation
            return activation.flow_task.reverse(
                "detail", args=[activation.process.pk, activation.task.pk]
            )

        return super().get_success_url()


class ProcessViewTemplateNames(object):
    """List of templates for a process view."""

    template_filename = None

    def get_template_names(self):
        if self.template_name is None:
            opts = self.flow_class.instance

            return (
                f"{opts.app_label}/{opts.flow_label}/{self.template_filename}",
                f"viewflow/workflow/{self.template_filename}",
            )
        else:
            return [self.template_name]


class TaskViewTemplateNames(object):
    """List of templates for a task view."""

    template_filename = None

    def get_template_names(self):
        if self.template_name is None:
            flow_task = self.request.activation.flow_task
            opts = flow_task.flow_class.instance
            assert not self.template_name

            return (
                f"{opts.app_label}/{opts.app_label}/{flow_task.name}_{self.template_filename}",
                f"{opts.app_label}/{opts.flow_label}/{self.template_filename}",
                f"viewflow/workflow/{self.template_filename}",
            )
        else:
            return [self.template_name]


class StoreRequestPathMixin:
    def dispatch(self, request, *args, **kwargs):
        request.session["vf-pin-location"] = request.get_full_path()
        return super().dispatch(request, *args, **kwargs)
