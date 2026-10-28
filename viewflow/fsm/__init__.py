"""Compatibility exports for the standalone django-fsm package."""

import django_fsm as _fsm
from django_fsm import *  # noqa: F401,F403
from django_fsm import __all__ as _core_all

# Load the compatibility submodule before assigning the chart function.
from .chart import chart  # noqa: F401

# The optional integrations are provided lazily through __getattr__.
__all__ = (*_core_all, "FlowAdminMixin", "FlowViewsMixin")  # noqa: F405


def __getattr__(name):
    return getattr(_fsm, name)
