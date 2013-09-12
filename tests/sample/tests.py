from django.test import TestCase
from sample.flow import Shipmentflow

class TDDTestCases(TestCase):
    def test_flow_meta_creation_succeed(self):
        self.assertTrue(hasattr(Shipmentflow, '_meta'))
