"""
Django compatibility utils
"""
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
        return app_config.module.__package__

    def get_containing_app_data(module):
        """
        Return app label and package string
        """
        app_config = apps.get_containing_app_config(module)
        return app_config.label, app_config.module.__package__

except ImportError:
    # djagno 1.6
    from django.db.models import loading

    def get_app_package(app_label):
        return loading.get_app(app_label).__package__

    def _get_containing_app(object_name):
        candidates = []
        for app_config in loading.get_apps():
            if object_name.startswith(app_config.__package__):
                subpath = object_name[len(app_config.__package__):]
                if subpath == '' or subpath[0] == '.':
                    candidates.append(app_config)
        if candidates:
            return sorted(candidates, key=lambda ac: -len(ac.__package__))[0]

    def get_containing_app_data(object_name):
        app = _get_containing_app(object_name)
        if app:
            return app.__package__.rsplit('.', 1)[-1], app.__package__
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
