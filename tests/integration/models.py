"""
Import test models to avoid weird migrations behavour in 1.8
"""
import django

if django.VERSION >= (1, 7):
    from .tests.test_contrib_celery import TestCeleryProcess  # NOQA
    from .tests.test_flow_gate_break import BrokenGateProcess  # NOQA

