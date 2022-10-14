from django.views.decorators.http import last_modified
from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from ... import chart


process_start_time = timezone.now()


class FlowChartView(generic.View):
    """Flow and Process chart View."""

    flow_class = None

    @method_decorator(
        last_modified(
            lambda *args, **kwargs: None
            if "process_pk" in kwargs
            else process_start_time
        )
    )
    def get(self, request, *args, **kwargs):
        process_pk = kwargs.get("process_pk")

        grid = chart.calc_layout_data(self.flow_class)
        if process_pk is not None:
            chart.calc_cell_status(self.flow_class, grid, process_pk)
        svg = chart.grid_to_svg(grid)

        return HttpResponse(svg, content_type="image/svg+xml")
