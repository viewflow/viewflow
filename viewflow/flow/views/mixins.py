from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class LoginRequiredMixin(object):
    """Mixin to check that user is authenticated."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):  # noqa D102
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class FlowViewPermissionMixin(object):
    """Mixin for flow views, check the view permission."""

    def dispatch(self, *args, **kwargs):  # noqa D102
        self.flow_class = kwargs['flow_class']
        return permission_required(self.flow_class.instance.view_permission_name)(
            super(FlowViewPermissionMixin, self).dispatch)(*args, **kwargs)


class FlowManagePermissionMixin(object):
    """Mixin for flow flow views, check flow manage permission."""

    def dispatch(self, *args, **kwargs):  # noqa D102
        self.flow_class = kwargs['flow_class']
        return permission_required(self.flow_class.instance.manage_permission_name)(
            super(FlowManagePermissionMixin, self).dispatch)(*args, **kwargs)


class FlowTaskManagePermissionMixin(object):
    """Mixin for flow task views, check flow manage permission."""

    def dispatch(self, *args, **kwargs):  # noqa D102
        self.flow_task = kwargs['flow_task']
        self.flow_class = self.flow_task.flow_class
        return permission_required(self.flow_class.instance.manage_permission_name)(
            super(FlowTaskManagePermissionMixin, self).dispatch)(*args, **kwargs)


class MessageUserMixin(object):
    """Notify a user using django messaging system."""

    def report(self, message, level=messages.INFO, fail_silently=True, **kwargs):
        """Send a notification with link to the current process or task.

        :param message: A message template.
        :param level: A level, one of https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-levels
        :param fail_silently: Raise a error if messaging framework is not installed.
        :param kwargs: Additional parametes used in format message templates.

        A `message_template` prepared by python `.format()`
        function. In addition to `kwargs`, the `{process}` and `{task}`
        parametes passed.
        
        Example::

            self.report('Task {task} from {process} has been completed.')

        """
        namespace = self.request.resolver_match.namespace

        process_url = reverse('{}:detail'.format(namespace), args=[self.activation.process.pk])
        process_link = '<a href="{process_url}">#{process_pk}</a>'.format(
            process_url=process_url,
            process_pk=self.activation.process.pk)

        task_url = self.activation.task.flow_task.get_task_url(
            self.activation.task, url_type='detail', user=self.request.user, namespace=namespace)
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
        """Notification about sucessful operation."""
        self.report(message, level=messages.SUCCESS, fail_silently=fail_silently, **kwargs)

    def error(self, message, fail_silently=True, **kwargs):
        """Notification about error."""
        self.report(message, level=messages.ERROR, fail_silently=fail_silently, **kwargs)


class FlowListMixin(object):
    """Mixin for list view contains multiple flows."""

    ns_map = None

    def __init__(self, *args, **kwargs):
        """
        Instantiate a view.

        :param ns_map: Dict{'flow_namespace': flow_class}
        """
        self.ns_map = kwargs.get('ns_map', {})
        super(FlowListMixin, self).__init__(*args, **kwargs)

    @property
    def flows(self):
        """List of flow classes."""
        return self.ns_map.values()
