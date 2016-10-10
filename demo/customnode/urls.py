from viewflow.flow.viewset import FlowViewSet
from .flows import DynamicSplitFlow


urlpatterns = FlowViewSet(DynamicSplitFlow).urls
