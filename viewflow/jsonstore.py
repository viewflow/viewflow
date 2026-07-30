# Copyright (c) 2017-2026, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

"""Backwards-compatible alias for the standalone ``django-jsonstore`` package.

The virtual JSON-backed model fields used to live here. They are maintained on
their own now -- https://github.com/viewflow/jsonstore -- and ``viewflow``
depends on that package, so ``from viewflow import jsonstore`` and
``import jsonstore`` give you the very same classes.
"""

from jsonstore import *  # noqa: F401,F403
from jsonstore import __all__  # noqa: F401
