"""Compatibility alias for :mod:`django_fsm.fields`."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("django_fsm.fields")
