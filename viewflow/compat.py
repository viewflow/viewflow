"""Django compatibility utils."""
from functools import WRAPPER_ASSIGNMENTS, update_wrapper

try:
    # django 1.8
    from django.template.library import TemplateSyntaxError, TagHelperNode, parse_bits  # NOQA
except:
    from django.template.base import TemplateSyntaxError, Node, parse_bits  # NOQA

    class TagHelperNode(Node):
        """
        Base class for tag helper nodes such as SimpleNode and InclusionNode.

        Manages the positional and keyword arguments to be passed to the decorated
        function.
        """

        def __init__(self, func, takes_context, args, kwargs):  # noqa D102
            self.func = func
            self.takes_context = takes_context
            self.args = args
            self.kwargs = kwargs

        def get_resolved_arguments(self, context):
            """Resolve all args from the template context."""
            resolved_args = [var.resolve(context) for var in self.args]
            if self.takes_context:
                resolved_args = [context] + resolved_args
            resolved_kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
            return resolved_args, resolved_kwargs


# djagno 1.7
from django.apps import apps


def get_app_package(app_label):
    """Return app package string."""
    app_config = apps.get_app_config(app_label)
    if not app_config:
        return None
    return app_config.module.__name__


def get_containing_app_data(module):
    """Return app label and package string."""
    app_config = apps.get_containing_app_config(module)
    if not app_config:
        return None, None
    return app_config.label, app_config.module.__name__


def get_all_related_objects(obj):
    """Backward releations to a model."""
    if hasattr(obj._meta, 'get_fields'):
        from django.db.models.fields.related import ForeignObjectRel
        return [field for field in obj._meta.get_fields() if isinstance(field, ForeignObjectRel)]
    else:
        # depricated in django 1.9
        return obj._meta.get_all_related_objects()

"""
Backbort method decorator from django 1.10 to django 1.8
"""


def available_attrs(fn):
    """
    Return the list of functools-wrappable attributes on a callable.
    This was required as a workaround for http://bugs.python.org/issue3445
    under Python 2.
    """
    return WRAPPER_ASSIGNMENTS


def method_decorator(decorator, name=''):
    """
    Converts a function decorator into a method decorator
    """
    # 'obj' can be a class or a function. If 'obj' is a function at the time it
    # is passed to _dec,  it will eventually be a method of the class it is
    # defined on. If 'obj' is a class, the 'name' is required to be the name
    # of the method that will be decorated.
    def _dec(obj):
        is_class = isinstance(obj, type)
        if is_class:
            if name and hasattr(obj, name):
                func = getattr(obj, name)
                if not callable(func):
                    raise TypeError(
                        "Cannot decorate '{0}' as it isn't a callable "
                        "attribute of {1} ({2})".format(name, obj, func)
                    )
            else:
                raise ValueError(
                    "The keyword argument `name` must be the name of a method "
                    "of the decorated class: {0}. Got '{1}' instead".format(
                        obj, name,
                    )
                )
        else:
            func = obj

        def decorate(function):
            """
            Apply a list/tuple of decorators if decorator is one. Decorator
            functions are applied so that the call order is the same as the
            order in which they appear in the iterable.
            """
            if hasattr(decorator, '__iter__'):
                for dec in decorator[::-1]:
                    function = dec(function)
                return function
            return decorator(function)

        def _wrapper(self, *args, **kwargs):
            @decorate
            def bound_func(*args2, **kwargs2):
                return func.__get__(self, type(self))(*args2, **kwargs2)
            # bound_func has the signature that 'decorator' expects i.e.  no
            # 'self' argument, but it is a closure over self so it can call
            # 'func' correctly.
            return bound_func(*args, **kwargs)
        # In case 'decorator' adds attributes to the function it decorates, we
        # want to copy those. We don't have access to bound_func in this scope,
        # but we can cheat by using it on a dummy function.

        @decorate
        def dummy(*args, **kwargs):
            pass
        update_wrapper(_wrapper, dummy)
        # Need to preserve any existing attributes of 'func', including the name.
        update_wrapper(_wrapper, func)

        if is_class:
            setattr(obj, name, _wrapper)
            return obj

        return _wrapper
    # Don't worry about making _dec look similar to a list/tuple as it's rather
    # meaningless.
    if not hasattr(decorator, '__iter__'):
        update_wrapper(_dec, decorator, assigned=available_attrs(decorator))
    # Change the name to aid debugging.
    if hasattr(decorator, '__name__'):
        _dec.__name__ = 'method_decorator(%s)' % decorator.__name__
    else:
        _dec.__name__ = 'method_decorator(%s)' % decorator.__class__.__name__
    return _dec
