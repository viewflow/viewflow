"""Viewflow - The Django extension for perfectionists with yesterday’s deadlines."""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from .this_object import this
from .utils import viewprop, Icon, DEFAULT

__title__ = "Django-Viewflow"
__version__ = "2.3.2"
__author__ = "Mikhail Podgurskiy"
__license__ = "AGPL"
__copyright__ = "Copyright 2018-2021 Mikhail Podgurskiy"

__all__ = ("this", "viewprop", "Icon", "DEFAULT")

default_app_config = "viewflow.apps.ViewflowConfig"

# Middleware auto-registration lives in ViewflowConfig.ready() -- the app
# registry isn't populated yet at this point, so apps.is_installed() (needed
# to recognize viewflow regardless of how it's spelled in INSTALLED_APPS)
# isn't safe to call here.
