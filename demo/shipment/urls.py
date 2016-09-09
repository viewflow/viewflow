from viewflow.flow import routers
from .flows import ShipmentFlow

urlpatterns = routers.FlowRouter(ShipmentFlow).urls
