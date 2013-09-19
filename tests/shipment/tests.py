import os
import tempfile
from django.test import TestCase
from viewflow.graphviz import diagram
from shipment.flow import Shipmentflow


class ShipmentFlowConformanceTests(TestCase):
    def test_diagram_creation_succeed(self):
        outdir = tempfile.mkdtemp()
        png_filename = os.path.join(outdir, 'output.png')

        diagram(Shipmentflow, png_filename)

        self.assertTrue(os.path.exists(png_filename))
