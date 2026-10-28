"""Compatibility alias for :mod:`django_fsm.typing`."""

import importlib
import sys

sys.modules[__name__] = importlib.import_module("django_fsm.typing")
