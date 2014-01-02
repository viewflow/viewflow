from django.conf.urls import patterns, url
from django.shortcuts import render
from django.utils.module_loading import autodiscover_modules


class FlowSite(object):
    """
    Instance for viewflow application
    """
    def __init__(self, name='flow', app_name='flow'):
        self._name = name
        self._app_name = app_name
        self._registry = {}  # Map process model -> flow

    def register(self, model, flow):
        self._registry[model] = flow

    def index(self, request):
        """
        Displays list of all installed flows page
        """
        app_dict = {}
        for model, flow in self._registry.items():
            app_label = model._meta.app_label
            flow_dict = {
                'name': 'TODO',
                'tasks_url': 'TODO',
                'start_url': 'TODO'
            }

            if app_label in app_dict:
                app_dict[app_label]['flows'].append(flow_dict)
            else:
                app_dict[app_label] = {
                    'name': app_label.title(),
                    'app_url': 'TODO',
                    'flows': [flow_dict]
                }

        # Sort the apps alphabetically
        app_list = list(app_dict.values())
        app_list.sort(key=lambda x: x['name'])

        # Sort the flows alphabetically within each app
        for app in app_list:
            app['flows'].sort(key=lambda x: x['name'])

        return render(request, 'viewflow/index.html', {
            'app_list': app_list
        })

    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^$', self.index, name='index'))  # noqa
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self._app_name, self._name

    def autodiscover(self):
        """
        Import all flows for <app>/flow.py
        """
        autodiscover_modules('flowsite', register_to=self)
