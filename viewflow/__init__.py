import copy
from collections import defaultdict
from importlib import import_module

from django.conf import settings
from django.conf.urls import patterns, url
from django.shortcuts import render
from django.utils.module_loading import module_has_submodule

from viewflow import flow
from viewflow.resolve import Resolver


this = flow.This()


class FlowMeta(object):
    """
    Flow options
    """
    def __init__(self, meta, nodes):
        self._meta = meta
        self._nodes_by_name = nodes

    def nodes(self):
        """
        Nodes iterator
        """
        return self._nodes_by_name.values()

    def node(self, name):
        """
        Get node by name
        """
        return self._nodes_by_name.get(name, None)


class FlowMetaClass(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(FlowMetaClass, cls).__new__(cls, name, bases, attrs)

        # set up flow tasks
        nodes = {name: attr for name, attr in attrs.items() if isinstance(attr, flow._Node)}

        for name, node in nodes.items():
            node.name = name

        resolver = Resolver(nodes)
        for node in nodes.values():
            resolver.resolve_children_links(node)

        incoming = defaultdict(lambda: [])  # node -> [incoming_nodes]
        for _, node in nodes.items():
            for outgoing_edge in node._outgoing():
                incoming[outgoing_edge.dst].append(outgoing_edge)
        for target, edges in incoming.items():
            target._incoming_edges = edges

        # set up workflow meta
        meta = getattr(new_class, 'Meta', None)
        new_class._meta = FlowMeta(meta, nodes)

        return new_class


class Flow(object, metaclass=FlowMetaClass):
    """
    Base class for flow definition
    """


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


site = FlowSite()


def autodiscover():
    """
    Import all flows for <app>/flow.py
    """
    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            before_import_registry = copy.copy(site._registry)
            import_module('%s.flow' % app)
        except:
            site._registry = before_import_registry
            if module_has_submodule(mod, 'flow'):
                raise
