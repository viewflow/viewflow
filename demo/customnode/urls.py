from viewflow.flow import routers
from .flows import DynamicSplitFlow


urlpatterns = routers.FlowRouter(DynamicSplitFlow).urls
