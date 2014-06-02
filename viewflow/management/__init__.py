from django.db.models import signals


def import_flows(app_config, **kwargs):
    """
    Pre-import flows to allow permissions auto-creation
    """
    try:
        __import__('{}.flows'.format(app_config.module.__name__))
    except ImportError:
        pass


signals.pre_migrate.connect(import_flows, dispatch_uid="viewflow.management.import_flows")
