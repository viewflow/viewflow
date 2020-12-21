from django.apps import AppConfig

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial licence defined in file 'COMM_LICENSE',
# which is part of this source code package.


class ViewflowConfig(AppConfig):
    """Default application config."""

    name = 'viewflow'
    label = 'viewflow_base'  # allow to user 'viewflow' label for 'viewflow.workflow'
