"""
Flow scenario based testing

with FlowTest(RestrictedUserFlow) as flow_test:

    flow_test.Task(Flow.start).User('xxx').Execute({xxx=1, yyy=2}) \
        .Assert(lambda t: t.owner='xxx') \
        .Assert(p: p.owner='yyy')

    with patch('web.service'):
        flow_test.Task(Flow.job),Execute()

    flow_test.User('aaa').Task(Flow.confirm).Execute({'confirm': 1})

"""
import inspect
try:
    from functools import singledispatch
except ImportError:
    from singledispatch import singledispatch

from django.contrib import auth
from django.utils.functional import cached_property
from django_webtest import WebTestMixin

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.signals import task_finished


@singledispatch
def flow_do(flow_node, test_task, **post_kwargs):
    """
    Executes flow task
    """
    raise NotImplementedError


@flow_do.register(flow.Start)  # NOQA
def _(flow_node, test_task, **post_kwargs):
    """
    Start flow process
    """
    url_args = test_task.url_args.copy()
    url_args.setdefault('task', None)
    url_args.setdefault('user', auth.authenticate(django_webtest_user=test_task.user))

    task_url = flow_node.get_task_url(url_type='execute', **url_args)

    form = test_task.app.get(task_url, user=test_task.user).form

    for key, value in post_kwargs.items():
        form[key] = value

    form.submit('start').follow()


@flow_do.register(flow.View)  # NOQA
def _(flow_node, test_task, **post_kwargs):
    """
    Assign if required and executes view task
    """
    task = test_task.flow_cls.task_cls._default_manager.get(
        flow_task=test_task.flow_task,
        status__in=[STATUS.NEW, STATUS.ASSIGNED])

    url_args = test_task.url_args.copy()
    url_args.setdefault('task', task)
    url_args.setdefault('user', auth.authenticate(django_webtest_user=test_task.user))

    # Assign
    if not task.owner:
        task_url = flow_node.get_task_url(url_type='assign', **url_args)
        form = test_task.app.get(task_url, user=test_task.user).form
        form = form.submit('assign').follow().form
        url_args['task'] = flow_node.flow_cls.task_cls._default_manager.get(pk=url_args['task'].pk)

    # Execute
    task_url = flow_node.get_task_url(url_type='execute', **url_args)
    form = test_task.app.get(task_url, user=test_task.user).form

    for key, value in post_kwargs.items():
        form[key] = value

    form.submit().follow()


@singledispatch
def flow_patch_manager(flow_node):
    """
    context manager for flow mock setup
    """
    return None


class FlowTaskTest(object):
    def __init__(self, app, flow_cls, flow_task):
        self.app = app
        self.flow_cls, self.flow_task = flow_cls, flow_task

        self.user = None
        self.url_args = {}

        self._task = None

    def task_finished(self, sender, **kwargs):
        if self._task is None:
            """
            First finished task is ours
            """
            assert self.flow_task == kwargs['task'].flow_task

            self._task = kwargs['task']

    @cached_property
    def process(self):
        """
        Reread process instanse from db, once after test call ends
        """
        return self.flow_cls.process_cls._default_manager.get(pk=self._task.process_id)

    @cached_property
    def task(self):
        """
        Reread task instanse from db, once after test call ends
        """
        return self.flow_cls.task_cls._default_manager.get(pk=self._task.pk)

    def Url(self, **kwargs):
        self.url_args = kwargs
        return self

    def User(self, user):
        self.user = user

        return self

    def Execute(self, data=None):
        if not data:
            data = {}

        task_finished.connect(self.task_finished)

        try:
            flow_do(self.flow_task, self, **data)
        finally:
            task_finished.disconnect(self.task_finished)
        assert self._task, 'Flow task {} not finished'.format(self.flow_task.name)

        return self

    def Assert(self, assertion, fail_message=None):
        """
        Assert task or process.

        It is possible to assert ether the task or related process by choosing
        a different arg name for the assertion function.

        Example::

            Assert(lambda t: t.finished)  # tests task
            Assert(lambda p: p.is_shipped)  # tests process

        :param assertion: assertion callable
        :type assertion: function
        :param fail_message: assertion fail message
        :return: self
        :rtype: FlowTaskTest
        """
        if not fail_message:
            fail_message = "Flow task {} post condition fails".format(self.flow_task.name)

        if callable(assertion):
            args = inspect.getargspec(assertion).args

            if args == ['p']:
                assert assertion(self.process), fail_message
            elif args == ['t']:
                assert assertion(self.task), fail_message
            else:
                raise ValueError('Invalid assertion args spec {}'.format(args))
        else:
            assert assertion, fail_message

        return self


class FlowTest(WebTestMixin):
    def __init__(self, flow_cls):
        self.flow_cls = flow_cls

        self.patch_managers = []
        for node in flow_cls._meta.nodes():
            manager = flow_patch_manager(node)
            if manager:
                self.patch_managers.append(manager)

    def Task(self, flow_task):
        return FlowTaskTest(self.app, self.flow_cls, flow_task)

    def __enter__(self):
        self._patch_settings()
        self.renew_app()
        for patch_manager in self.patch_managers:
            patch_manager.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self._unpatch_settings()
        for patch_manager in self.patch_managers:
            patch_manager.__exit__()
