"""
Import test models to avoid weird migrations behavour in 1.8
"""
from .tests.test_contrib_celery import TestCeleryProcess  # NOQA
from .tests.test_flow_gate_break import BrokenGateProcess  # NOQA
