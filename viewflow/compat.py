"""
Django compatibility utils
"""
try:
    from unittest import mock  # NOQA
except ImportError:
    import mock  # NOQA

try:
    from django.utils.module_loading import import_string  # NOQA
except:
    # django 1.6/1.7
    from django.utils.module_loading import import_by_path as import_string  # NOQA

try:
    from django.template.library import TemplateSyntaxError, TagHelperNode, parse_bits  # NOQA
except:
    from django.template.base import TemplateSyntaxError, Node, parse_bits  # NOQA

    class TagHelperNode(Node):
        def __init__(self, func, takes_context, args, kwargs):
            self.func = func
            self.takes_context = takes_context
            self.args = args
            self.kwargs = kwargs

        def get_resolved_arguments(self, context):
            resolved_args = [var.resolve(context) for var in self.args]
            if self.takes_context:
                resolved_args = [context] + resolved_args
            resolved_kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
            return resolved_args, resolved_kwargs

try:
    # djagno 1.7
    from django.apps import apps
    from django.utils.deconstruct import deconstructible  # NOQA
    from django.utils.module_loading import autodiscover_modules  # NOQA

    def get_app_package(app_label):
        """
        Return app package string
        """
        app_config = apps.get_app_config(app_label)
        if not app_config:
            return None
        return app_config.module.__name__

    def get_containing_app_data(module):
        """
        Return app label and package string
        """
        app_config = apps.get_containing_app_config(module)
        if not app_config:
            return None, None
        return app_config.label, app_config.module.__name__

    def manager_from_queryset(manager_class, queryset_class, class_name=None):
        return manager_class.from_queryset(queryset_class, class_name=class_name)

except ImportError:
    # djagno 1.6 backport
    import inspect
    from django.db.models import loading
    from django.utils import six

    def get_app_package(app_label):
        app_config = loading.get_app(app_label)
        if not app_config:
            return None
        if app_config.__package__ is None:
            app_config.__package__ = app_config.__name__.rpartition('.')[0]
        if app_config.__package__.endswith('.models'):
            return app_config.__package__[0:-len('.models')]
        return app_config.__package__

    def _get_containing_app_package(object_name):
        candidates = []
        for app_config in loading.get_apps():
            if app_config.__package__ is None:
                app_config.__package__ = app_config.__name__.rpartition('.')[0]

            if app_config.__package__.endswith('.models'):
                package = app_config.__package__[0:-len('.models')]
            else:
                package = app_config.__package__

            if object_name.startswith(package):
                subpath = object_name[len(package):]
                if subpath == '' or subpath[0] == '.':
                    candidates.append(package)
        if candidates:
            return sorted(candidates, key=lambda ac: -len(ac))[0]

    def get_containing_app_data(object_name):
        package = _get_containing_app_package(object_name)
        if package:
            return package.rsplit('.', 1)[-1], package
        return None, None

    def deconstructible(cls):
        """
        Deconstructible decorator stub
        """
        return cls

    def autodiscover_modules(*args, **kwargs):
        import copy
        from django.conf import settings
        from django.utils.importlib import import_module
        from django.utils.module_loading import module_has_submodule

        register_to = kwargs.get('register_to')

        for app in settings.INSTALLED_APPS:
            mod = import_module(app)

            for module_to_search in args:
                if register_to:
                    before_import_registry = copy.copy(register_to._registry)

                try:
                    import_module('%s.%s' % (app, module_to_search))
                except:
                    if register_to:
                        register_to._registry = before_import_registry

                    if module_has_submodule(mod, module_to_search):
                        raise

    def _get_queryset_methods(manager_class, queryset_class):
        def create_method(name, method):
            def manager_method(self, *args, **kwargs):
                return getattr(self.get_queryset(), name)(*args, **kwargs)
            manager_method.__name__ = method.__name__
            manager_method.__doc__ = method.__doc__
            return manager_method

        new_methods = {}
        # Refs http://bugs.python.org/issue1785.
        predicate = inspect.isfunction if six.PY3 else inspect.ismethod
        for name, method in inspect.getmembers(queryset_class, predicate=predicate):
            # Only copy missing methods.
            if hasattr(manager_class, name):
                continue
            # Only copy public methods or methods with the attribute `queryset_only=False`.
            queryset_only = getattr(method, 'queryset_only', None)
            if queryset_only or (queryset_only is None and name.startswith('_')):
                if name != '_update':  # django 1.6 have no queryset_only attrubutes on methods
                    continue
            elif name == 'delete':
                continue
            # Copy the method onto the manager.
            new_methods[name] = create_method(name, method)

        # Fix get_queryset
        def get_queryset(self):
            return self._queryset_class(self.model, using=self._db)
        new_methods['get_queryset'] = get_queryset
        return new_methods

    def manager_from_queryset(manager_class, queryset_class, class_name=None):
        if class_name is None:
            class_name = '%sFrom%s' % (manager_class.__name__, queryset_class.__name__)
        class_dict = {
            '_queryset_class': queryset_class,
        }
        class_dict.update(_get_queryset_methods(manager_class, queryset_class))
        return type(class_name, (manager_class,), class_dict)


def get_all_related_objects(obj):
    if hasattr(obj._meta, 'get_fields'):
        from django.db.models.fields.related import ForeignObjectRel
        return [field for field in obj._meta.get_fields() if isinstance(field, ForeignObjectRel)]
    else:
        # depricated in django 1.9
        return obj._meta.get_all_related_objects()
