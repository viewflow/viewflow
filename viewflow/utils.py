def get_flow_namespace(flow_class, base_namespace, ns_map=None):
    """Construct flow namespace from relative `ns_map` and current `base_namespace`."""
    if ns_map:
        ns = ns_map.get(flow_class) or ns_map.get(type(flow_class))
        if ns:
            return f'{base_namespace}:{ns}' if base_namespace else ns
    return base_namespace


def is_owner(owner, user):
    """Check user instances and subclasses for equility."""
    return isinstance(user, owner.__class__) and owner.pk == user.pk
