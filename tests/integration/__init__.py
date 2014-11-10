import sys
import unittest


integration_test = unittest.skipIf(
    not [arg for arg in sys.argv if arg.startswith('tests.integration')],
    reason='Integration Test')
