from django.test import TestCase

from viewflow import this
from viewflow.workflow import Flow, flow, lock
from viewflow.workflow.checks import check_join_nodes_require_a_real_lock


def _noop(activation):
    pass


class UnsafeJoinFlow(Flow):  # noqa: D101
    # Default lock_impl (no_lock) + a Join node -- unsafe.
    start = flow.StartHandle().Next(this.split)
    split = flow.Split().Next(this.a).Next(this.b)
    a = flow.Function(_noop).Next(this.join)
    b = flow.Function(_noop).Next(this.join)
    join = flow.Join().Next(this.end)
    end = flow.End()


class SafeJoinFlow(Flow):  # noqa: D101
    lock_impl = lock.select_for_update_lock

    start = flow.StartHandle().Next(this.split)
    split = flow.Split().Next(this.a).Next(this.b)
    a = flow.Function(_noop).Next(this.join)
    b = flow.Function(_noop).Next(this.join)
    join = flow.Join().Next(this.end)
    end = flow.End()


class NoJoinFlow(Flow):  # noqa: D101
    # Default lock_impl (no_lock), but no Join node -- fine.
    start = flow.StartHandle().Next(this.func)
    func = flow.Function(_noop).Next(this.end)
    end = flow.End()


class UnregisteredAppJoinFlow(Flow):  # noqa: D101
    # Same shape as UnsafeJoinFlow, but its __module__ is rewritten below
    # to simulate a flow defined outside any INSTALLED_APPS entry -- e.g.
    # demo/charts.py in the demo project, which is never itself
    # registered as an app (only real, deployable app-owned flows are).
    start = flow.StartHandle().Next(this.split)
    split = flow.Split().Next(this.a).Next(this.b)
    a = flow.Function(_noop).Next(this.join)
    b = flow.Function(_noop).Next(this.join)
    join = flow.Join().Next(this.end)
    end = flow.End()


UnregisteredAppJoinFlow.__module__ = "not_a_registered_app.flows"


class Test(TestCase):
    def _flagged_flows(self):
        warnings = check_join_nodes_require_a_real_lock(None)
        return {w.obj for w in warnings}

    def test_flags_a_flow_with_a_join_node_and_the_default_lock(self):
        self.assertIn(UnsafeJoinFlow, self._flagged_flows())

    def test_does_not_flag_a_flow_with_a_real_lock(self):
        self.assertNotIn(SafeJoinFlow, self._flagged_flows())

    def test_does_not_flag_a_flow_without_a_join_node(self):
        self.assertNotIn(NoJoinFlow, self._flagged_flows())

    def test_stringifying_warnings_does_not_throw_for_a_flow_outside_any_app(self):
        # get_flow_ref (used by Flow's own __str__) raises FlowRuntimeError
        # for a flow class whose module isn't under any INSTALLED_APPS
        # entry. Django's `check` management command formats warnings by
        # calling str() on each one, which calls str() on `obj` --
        # crashing manage.py check/runserver entirely for a project that
        # (legitimately) defines demo/decorative flows outside any app,
        # like demo/charts.py's diagram-only flows.
        warnings = check_join_nodes_require_a_real_lock(None)
        for warning in warnings:
            str(warning)  # must not raise
