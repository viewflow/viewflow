from viewflow.flow import routers
from .flows import HelloWorldFlow

urlpatterns = routers.FlowRouter(HelloWorldFlow).urls
