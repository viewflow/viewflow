from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError
from viewflow.workflow import chart
from viewflow.workflow.fields import import_flow_by_ref


class Command(BaseCommand):
    help = "Export flow graph"

    def add_arguments(self, parser):
        parser.add_argument(
            "flow_label",
            nargs=1,
            type=str,
            help="Flow label, i.e. app_label/flows.MyFlow",
        )

        parser.add_argument(
            "--output",
            "-o",
            action="store",
            dest="output",
            help="Render output to a file",
        )

        parser.add_argument(
            "--process_pk",
            "-pk",
            action="store",
            dest="process",
            help="Draw process instance state",
        )

        parser.add_argument(
            "--format",
            dest="format",
            action="store",
            default="svg",
            help="Export format (svg or bpmn)",
        )

    def handle(self, **options):
        flow_class = import_flow_by_ref(options["flow_label"][0])

        result = ""
        process_pk = options.get("process")
        output_format = options.get("format")
        if output_format == "svg":
            grid = chart.calc_layout_data(flow_class)
            if process_pk is not None:
                chart.calc_cell_status(flow_class, grid, process_pk)
            result = chart.grid_to_svg(grid)
        elif output_format == "bpmn":
            grid = chart.calc_layout_data(
                flow_class, edge_start_gap_size=0, edge_end_gap_size=0
            )
            if process_pk is not None:
                chart.calc_cell_status(flow_class, grid, process_pk)
            result = chart.grid_to_bpmn(grid)
        else:
            CommandError("Unknown output format {}".format(output_format))

        filename = options.get("output")
        if filename:
            with open(filename, "w") as output:
                output.write(result)
        else:
            print(result)
