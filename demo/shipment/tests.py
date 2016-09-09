from django.conf.urls import include, url
from django.test import TestCase

from viewflow.models import Task
from viewflow.flow import routers
from viewflow.test import FlowTest

from .flows import ShipmentFlow
from .models import Carrier


class Test(TestCase):
    fixtures = ['shipment/default_data.json']

    sample_shipment = {
        'shipment_no': '#TST-20140101-1',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@doe.com',
        'phone': '+1-555000111',
        'address': 'Nowhere St, 21',
        'zipcode': '05501',
        'city': 'Washington',
        'state': 'NY',
        'country': 'Unated states'
    }

    def task(self, process, flow_task):
        return Task.objects.get(process=process, flow_task=flow_task)

    def setUp(self):
        self.default_carrier = Carrier.objects.get(name=Carrier.DEFAULT)
        self.special_carrier = Carrier.objects.exclude(name=Carrier.DEFAULT)[0]

    def test_normal_post_succeed(self):
        with FlowTest(ShipmentFlow, 'shipment') as flow:
            # Clerk start process
            flow.Task(ShipmentFlow.start).User('shipment/clerk') \
                .Execute(self.sample_shipment) \
                .Assert(lambda p: p.created is not None) \
                .Assert(lambda p: self.task(p, ShipmentFlow.start).owner.username == 'shipment/clerk')

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
        with FlowTest(ShipmentFlow, 'shipment') as flow:
            # Clerk start process
            flow.Task(ShipmentFlow.start).User('shipment/clerk') \
                .Execute(self.sample_shipment) \
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

urlpatterns = [
    # shipment
    url(r'^shipment/', include(routers.FlowRouter(ShipmentFlow).urls, namespace='shipment')),
]


try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
