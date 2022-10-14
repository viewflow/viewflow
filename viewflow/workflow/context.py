import threading


_context_stack = threading.local()


class Context(object):
    """Thread-local activation context, dynamically scoped.

    :keyword propagate_exception: If True, on activation failure
                                  exception will be propagated to
                                  previous activation. If False,
                                  current task activation will be
                                  marked as failed.


    Usage ::

        with Context(propagate_exception=False):
             print(context.propagate_exception)  # prints 'False'
        print(context.propagate_exception)  # prints default 'True'

    """

    def __init__(self, default=None, **kwargs):  # noqa D102
        self.default = default
        self.current_context_data = kwargs

    def __getattr__(self, name):
        stack = []

        if hasattr(_context_stack, 'data'):
            stack = _context_stack.data

        for scope in reversed(stack):
            if name in scope:
                return scope[name]

        if name in self.default:
            return self.default[name]

        raise AttributeError(name)

    def __enter__(self):
        if not hasattr(_context_stack, 'data'):
            _context_stack.data = []
        _context_stack.data.append(self.current_context_data)

    def __exit__(self, t, v, tb):
        _context_stack.data.pop()

    @staticmethod
    def create(**kwargs):  # noqa D102
        return Context(default=kwargs)


context = Context.create(propagate_exception=True)
