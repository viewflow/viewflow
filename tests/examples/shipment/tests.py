import os
import tempfile

from django.test import TestCase
from viewflow.graphviz import diagram
from viewflow.test import FlowTest

from examples.shipment.flows import ShipmentFlow
from examples.shipment.models import Carrier


class ShipmentFlowDiagrammTests(TestCase):
    def test_diagram_creation_succeed(self):
        outdir = tempfile.mkdtemp()
        png_filename = os.path.join(outdir, 'output.png')

        diagram(ShipmentFlow, png_filename)

        self.assertTrue(os.path.exists(png_filename))


class ShipmentFlowTests(TestCase):
    def setUp(self):
        self.default_carrier = Carrier.objects.get(name=Carrier.DEFAULT)
        self.special_carrier = Carrier.objects.exclude(name=Carrier.DEFAULT)[0]

    def _test_normal_post_succeed(self):
        with FlowTest(ShipmentFlow) as flow:
            # Clerk start process
            flow.Task(ShipmentFlow.start).User('shipment/clerk') \
                .Execute({'goods_tag': 'TST123'}) \
                .Assert(lambda p: p.created is not None)

            # Clerk decides that is special shipment post
            flow.Task(ShipmentFlow.shipment_type).User('shipment/clerk') \
                .Execute({'carrier': self.special_carrier.pk}) \
                .Assert(lambda p: not p.is_normal_post())

            # Clerk inputs carrier quote
            flow.Task(ShipmentFlow.request_quotes).User('shipment/clerk') \
                .Execute({'carrier_quote': 1000}) \
                .Assert(lambda p: p.shipment.carrier_quote == 1000)

            # Worker package goods
            flow.Task(ShipmentFlow.package_goods).User('shipment/worker') \
                .Execute()

            # Worker added paperwork and moved package out
            flow.Task(ShipmentFlow.move_package).User('shipment/worker') \
                .Execute() \
                .Assert(lambda p: p.finished is not None)

    def test_insured_post_succeed(self):
        with FlowTest(ShipmentFlow) as flow:
            # Clerk start process
            flow.Task(ShipmentFlow.start).User('shipment/clerk') \
                .Execute({'goods_tag': 'TST123'}) \
                .Assert(lambda p: p.created is not None)

            # Clerk decides that is normal shipment post
            flow.Task(ShipmentFlow.shipment_type).User('shipment/clerk') \
                .Execute({'carrier': self.default_carrier.pk}) \
                .Assert(lambda p: p.is_normal_post())

            # Clerk decides that extra insurance required
            flow.Task(ShipmentFlow.check_insurance).User('shipment/clerk') \
                .Execute({'need_insurance': True}) \
                .Assert(lambda p: p.need_extra_insurance())

            # Clerk fills post label
            flow.Task(ShipmentFlow.fill_post_label).User('shipment/clerk') \
                .Execute({'post_label': 'Test label'}) \
                .Assert(lambda p: p.shipment.post_label == 'Test label')

            # Worker package goods
            flow.Task(ShipmentFlow.package_goods).User('shipment/worker') \
                .Execute()

            # Manager takes extra insurance
            flow.Task(ShipmentFlow.take_extra_insurance).User('shipment/manager') \
                .Execute({'company_name': 'Test company',
                          'cost': 100}) \
                .Assert(lambda p: p.shipment.insurance.company_name == 'Test company')

            # Worker added paperwork and moved package out
            flow.Task(ShipmentFlow.move_package).User('shipment/worker') \
                .Execute() \
                .Assert(lambda p: p.finished is not None)
