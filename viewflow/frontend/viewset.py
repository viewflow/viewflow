from ..flow.viewset import FlowViewSet as BaseFlowViewSet
from .views import ProcessListView


class FlowViewSet(BaseFlowViewSet):
    process_list_view = [
        r'^$',
        ProcessListView.as_view(),
        'index'
    ]
