from django.test import TestCase
from viewflow import flow
from viewflow.base import Flow, this


class BaseFlow(Flow):
    start = flow.StartFunction().Next(this.end)
    handle = flow.Handler(this.handler_execute)
    end = flow.End()

    def handler_execute(self, activation):
        raise NotImplementedError


class FlowMixin(object):
    notify_admins = flow.Handler(this.send_alert).Next(this.notify_users)
    notify_users = flow.Handler(this.send_alert)


class ChildFlow(FlowMixin, BaseFlow):
    start = BaseFlow.start.Next(this.alert)
    alert = flow.Function(this.send_alert).Next(this.notify_admins)
    notify_users = FlowMixin.notify_users.Next(this.end)

    def handler_execute(self, activation):
        raise NotImplementedError

    def send_alert(self, activation):
        activation.prepare()
        activation.done()


class Test(TestCase):
    def test_base_flow_unchanged(self):
        self.assertEqual(BaseFlow.start._next, BaseFlow.end)

    def test_child_flow_overides_base_node(self):
        self.assertEqual(ChildFlow.alert._next, ChildFlow.notify_admins)
        self.assertEqual(ChildFlow.notify_users._next, ChildFlow.end)

    def test_child_flow_contains_all_urls(self):
        patterns_names = sorted([pat.name for pat in ChildFlow.instance.urls.url_patterns])
        self.assertEqual(patterns_names, sorted([
            'alert__perform', 'alert__cancel', 'alert__undo', 'alert__detail',
            'end__perform', 'end__cancel', 'end__undo', 'end__detail',
            'notify_admins__perform', 'notify_admins__cancel', 'notify_admins__undo',
            'notify_admins__detail', 'notify_users__perform', 'notify_users__cancel',
            'notify_users__undo', 'notify_users__detail', 'start__perform',
            'start__cancel', 'start__undo', 'start__detail',
            'handle__cancel', 'handle__undo', 'handle__detail', 'handle__perform']))

    def test_handle_proper_initialized(self):
        self.assertEqual(ChildFlow.handle.handler, ChildFlow.instance.handler_execute)
