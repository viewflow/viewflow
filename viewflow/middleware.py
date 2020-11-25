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
            site, app, viewset = extra.get('site'), extra.get('app'), extra.get('viewset')

            if site:
                if not site.has_perm(request.user):
                    raise PermissionDenied

            if app:
                if not app.has_perm(request.user):
                    raise PermissionDenied

            if viewset:
                if hasattr(viewset, 'has_perm') and not viewset.has_perm(request.user):
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


class TurbolinksMiddleware(object):
    """
    Send the `Turbolinks-Location` header in response to a visit that was redirected,
    and Turbolinks will replace the browser’s topmost history entry .
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        is_turbolinks = request.META.get('HTTP_TURBOLINKS_REFERRER')
        is_response_redirect = response.has_header('Location')

        if is_turbolinks:
            if is_response_redirect:
                location = response['Location']
                prev_location = request.session.pop('_turbolinks_redirect_to', None)
                if prev_location is not None:
                    # relative subsequent redirect
                    if location.startswith('.'):
                        location = prev_location.split('?')[0] + location
                request.session['_turbolinks_redirect_to'] = location
            else:
                if request.session.get('_turbolinks_redirect_to'):
                    location = request.session.pop('_turbolinks_redirect_to')
                    response['Turbolinks-Location'] = location
        return response
