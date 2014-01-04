import os
import tempfile
from django.test import TestCase
from viewflow.graphviz import diagram
from shipment.flows import ShipmentFlow


class ShipmentFlowConformanceTests(TestCase):
    def test_diagram_creation_succeed(self):
        outdir = tempfile.mkdtemp()
        png_filename = os.path.join(outdir, 'output.png')

        diagram(ShipmentFlow, png_filename)

        self.assertTrue(os.path.exists(png_filename))
