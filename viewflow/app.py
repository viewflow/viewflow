import inspect
from importlib import import_module

from django.apps import apps, AppConfig
from django.utils.module_loading import module_has_submodule


FLOWS_MODULE_NAME = 'flows'


class ViewflowConfig(AppConfig):
    name = 'viewflow'

    def __init__(self, app_name, app_module):
        super(ViewflowConfig, self).__init__(app_name, app_module)
        self.flows = {}  # map app_label -> [flow class]

    def ready(self):
        from viewflow import Flow

        for app_config in apps.get_app_configs():
            if app_config != self and module_has_submodule(app_config.module, FLOWS_MODULE_NAME):
                flows_module_name = '%s.%s' % (app_config.name, FLOWS_MODULE_NAME)
                flows_module = import_module(flows_module_name)

                def _is_flow_cls(cls):
                    return inspect.isclass(cls) \
                        and cls != Flow \
                        and issubclass(cls, Flow)

                for flow_cls_name, flow_cls in inspect.getmembers(flows_module, _is_flow_cls):
                    if app_config.label not in self.flows:
                        self.flows[app_config.label] = [flow_cls]
                    else:
                        self.flows[app_config.label].append(flow_cls)
