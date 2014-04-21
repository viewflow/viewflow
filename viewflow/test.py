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
from singledispatch import singledispatch
from django_webtest import WebTestMixin

from viewflow import flow
from viewflow.signals import task_finished
from viewflow.urls import node_url_reverse


@singledispatch
def flow_do(flow_node, app, **post_kwargs):
    """
    Executes flow task
    """
    raise NotImplementedError


@flow_do.register(flow.Start)  # NOQA
def _(flow_node, app, **post_kwargs):
    task_url = node_url_reverse(flow_node)
    form = app.get(task_url)
    form.submit().follow()


@flow_do.register(flow.View)  # NOQA
def _(flow_node, app, **post_kwargs):
    pass


@flow_do.register(flow.Job)  # NOQA
def _(flow_node, app, **post_kwargs):
    pass


@singledispatch
def flow_patch_manager(flow_node):
    """
    context manager for flow mock setup
    """
    return None


@flow_patch_manager.register(flow.Job)  # NOQA
def _(flow_node):
    pass


class FlowTaskTest(object):
    def __init__(self, flow_cls, flow_task):
        self.flow_cls, self.flow_task = flow_cls, flow_task
        self.process, self.task = None, None

        self.user, self.user_lookup = None, {}
        self.url_args = {}

    def task_finished(self, sender, **kwargs):
        if self.task is None:
            """
            First finished task is ours
            """
            assert self.flow_task == kwargs['task'].flow_task

            self.task = kwargs['task']
            self.process = kwargs['process']

    def Url(self, **kwargs):
        self.url_args = kwargs
        return self

    def User(self, user=None, **user_lookup):
        self.user = user
        self.user_lookup = user_lookup

        return self

    def Execute(self, data):
        task_finished.connect(self.task_finished)
        flow_do(self.flow_task, **data)
        task_finished.disconnect(self.task_finished)
        assert self.task, 'Flow task {} not finished'.format(self.flow_task.name)

        return self

    def Assert(self, assertion):
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
        for node in flow_cls.nodes():
            manager = flow_patch_manager(node)
            if manager:
                self.patch_managers.append(manager)

    def Task(self, flow_task):
        return FlowTaskTest(self.flow_cls, flow_task)

    def __enter__(self):
        self._patch_settings()
        self.renew_app()
        for patch_manager in self.patch_managers:
            patch_manager.__enter__()

    def __exit__(self, type, value, traceback):
        self._unpatch_settings()
        for patch_manager in self.patch_managers:
            patch_manager.__exit__()
