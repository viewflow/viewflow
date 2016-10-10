from viewflow.flow.viewset import FlowViewSet
from .flows import ShipmentFlow

urlpatterns = FlowViewSet(ShipmentFlow).urls
