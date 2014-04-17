"""
Flow scenario based testing

with FlowTest(RestrictedUserFlow) as flow_test:
    flow_test.User('xxx').Do(Flow.start, {
         xxx=1,
         yyy=2}) \
        .Assert(lambda t: t.owner='xxx') \
        .Assert(p: p.owner='yyy')

    with patch('web.service'):
        flow_test.Do(Flow.job)

    flow_test.User('aaa').Do(Flow.confirm, {'confirm': 1})

"""
from singledispatch import singledispatch
from viewflow import flow


@singledispatch
def flow_do(flow_node, *args, **kwargs):
    """
    Executes flow task
    """
    raise NotImplementedError


@flow_do.register(flow.View)  # NOQA
def _(flow_node, client, **post_kwargs):
    pass


@flow_do.register(flow.Job)  # NOQA
def _(flow_node, client, **post_kwargs):
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


class FlowTestTask(object):
    """
    """
    def User(self, user=None, **user_lookup):
        pass

    def Do(self):
        pass


class FlowTest(object):
    """
    """
    def __init__(self, flow_cls):
        self.flow_cls = flow_cls

        self.patch_managers = []
        for node in flow_cls.nodes():
            manager = flow_patch_manager(node)
            if manager:
                self.patch_managers.append(manager)

    def __enter__(self):
        for patch_manager in self.patch_managers:
            patch_manager.__enter__()

    def __exit__(self, type, value, traceback):
        for patch_manager in self.patch_managers:
            patch_manager.__exit__()
