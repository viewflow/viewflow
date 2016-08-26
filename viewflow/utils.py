def get_flow_namespace(flow_class, base_namespace, ns_map=None):
    """
    Construct flow namespace from relative `ns_map # { namespace: FlowClass }` and current `base_namespace`
    """
    if ns_map:
        for ns, map_class in ns_map.items():
            if isinstance(flow_class, map_class) or map_class == flow_class:
                return '{}:{}'.format(base_namespace, ns) if base_namespace else ns
    return base_namespace
