from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class FlowViewPermissionMixin(object):
    flow_cls = None

    def dispatch(self, *args, **kwargs):
        self.flow_cls = kwargs.get('flow_cls', self.flow_cls)
        return permission_required(self.flow_cls.instance.view_permission_name)(
            super(FlowViewPermissionMixin, self).dispatch)(*args, **kwargs)


class FlowManagePermissionMixin(object):
    flow_cls = None

    def dispatch(self, *args, **kwargs):
        self.flow_cls = kwargs.get('flow_cls', self.flow_cls)
        return permission_required(self.flow_cls.instance.manage_permission_name)(
            super(FlowManagePermissionMixin, self).dispatch)(*args, **kwargs)


class MessageUserMixin(object):
    def report(self, message, level=messages.INFO, fail_silently=True, **kwargs):
        namespace = self.request.resolver_match.namespace

        process_url = reverse('{}:detail'.format(namespace), args=[self.activation.process.pk])
        process_link = '<a href="{process_url}">#{process_pk}</a>'.format(
            process_url=process_url,
            process_pk=self.activation.process.pk)

        task_url = self.activation.task.flow_task.get_task_url(
            self.activation.task, url_type='details', user=self.request.user, namespace=namespace)
        task_link = '<a href="{task_url}">#{task_pk}</a>'.format(
            task_url=task_url,
            task_pk=self.activation.task.pk)

        kwargs.update({
            'process': process_link,
            'task': task_link
        })
        message = mark_safe(_(message).format(**kwargs))

        messages.add_message(self.request, level, message, fail_silently=fail_silently)

    def success(self, message, fail_silently=True, **kwargs):
        self.report(message, level=messages.SUCCESS, fail_silently=fail_silently, **kwargs)

    def error(self, message, fail_silently=True, **kwargs):
        self.report(message, level=messages.ERROR, fail_silently=fail_silently, **kwargs)
