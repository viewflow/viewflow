# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from django.core.exceptions import PermissionDenied


class SiteMiddleware(object):
    """
    Set `site` and `app` attributes on request.resolver_match object.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not hasattr(request, 'user'):
            raise ValueError(
                'No `request.user` found. `django.contrib.auth.context_processors.auth` '
                'missing or `material.middleware.site included before it.` '
                'You need to add auth middleware or change middlewares order.')
        match = request.resolver_match
        if match:
            extra = getattr(match.url_name, 'extra', {})
            site, app = extra.get('site'), extra.get('app')

            if site:
                if not site.has_view_permission(request.user):
                    raise PermissionDenied

            if app:
                if not app.has_view_permission(request.user):
                    raise PermissionDenied

            for name, value in extra.items():
                setattr(request.resolver_match, name, value)

        return None

    def process_template_response(self, request, response):
        app = getattr(request.resolver_match, 'app', None)
        if app:
            app_context = app.get_context_data(request)
            for key, value in app_context.items():
                if key in response.context_data:
                    raise ValueError(f'App context key {key} clashes with view response context')
                else:
                    response.context_data[key] = value
        return response


def HotwireTurboMiddleware(get_response):
    def middleware(request):
        response = get_response(request)
        if request.method == 'POST' and request.META.get('HTTP_X_REQUEST_FRAMEWORK') == 'Turbo':
            if response.status_code == 200:
                response.status_code = 422
            elif response.status_code == 301:
                response.status_code = 303
        return response

    return middleware
