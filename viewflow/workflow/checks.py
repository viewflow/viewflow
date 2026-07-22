"""System checks warning about unsafe workflow configuration."""

from django.core.checks import Warning, register


def _all_flow_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _all_flow_subclasses(subclass)


@register()
def check_join_nodes_require_a_real_lock(app_configs, **kwargs):
    """Join correctness depends on lock_impl serializing concurrent branch
    completions. With the default `no_lock`, two branches finishing at the
    same time can both pass the "does a join task already exist" check
    before either creates one, producing two join tasks and a
    FlowRuntimeError instead of joining once.
    """
    from viewflow.utils import get_containing_app_data

    from .base import Flow
    from .lock import no_lock
    from .nodes.join import Join

    errors = []
    for flow_class in _all_flow_subclasses(Flow):
        if flow_class.lock_impl is not no_lock:
            continue
        # A flow class outside any INSTALLED_APPS entry (e.g. a
        # diagram-only flow defined at the project root, not inside a
        # real app) can't be referenced via get_flow_ref/str(flow_class)
        # -- and Warning(obj=flow_class) below calls exactly that when
        # Django formats check output, crashing `manage.py check`
        # entirely. Skip flows that aren't part of a real, deployable app.
        module = f"{flow_class.__module__}.{flow_class.__name__}"
        app_label, _ = get_containing_app_data(module)
        if app_label is None:
            continue
        has_join = any(isinstance(node, Join) for node in flow_class.instance.nodes())
        if has_join:
            errors.append(
                Warning(
                    f"{flow_class.__name__} has a Join node but uses the "
                    "default lock_impl=no_lock, which is unsafe for "
                    "concurrent branch completions.",
                    hint=(
                        "Set lock_impl to a real lock, e.g. "
                        "viewflow.workflow.lock.select_for_update_lock or "
                        "cache_lock, on the flow class."
                    ),
                    obj=flow_class,
                    id="viewflow.W001",
                )
            )
    return errors
