def get_flow_namespace(flow_class, base_namespace, ns_map=None):
    """Construct flow namespace from relative `ns_map` and current `base_namespace`."""
    if ns_map:
        ns = ns_map.get(flow_class) or ns_map.get(type(flow_class))
        if ns:
            return '{}:{}'.format(base_namespace, ns) if base_namespace else ns
    return base_namespace
