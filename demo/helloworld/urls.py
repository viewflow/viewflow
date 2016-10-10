from viewflow.flow.viewset import FlowViewSet
from .flows import HelloWorldFlow


urlpatterns = FlowViewSet(HelloWorldFlow).urls
