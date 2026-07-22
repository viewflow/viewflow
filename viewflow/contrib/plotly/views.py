import functools
import json
import re
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView


def dash_view_permission_required(view_func):
    """Require an authenticated user with view permission on the Dashboard.

    Dash endpoints have no built-in auth of their own, and Dashboard's
    default `has_view_permission` (inherited from AppMenuMixin, since
    Dashboard isn't an Application) is always True -- so without this,
    an anonymous user could read the dashboard layout/data and invoke
    registered callbacks.
    """

    @functools.wraps(view_func)
    def wrapper(request, viewset, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if not viewset.has_view_permission(request.user):
            raise PermissionDenied
        return view_func(request, viewset, *args, **kwargs)

    return wrapper


def _extract_urls(data):
    """
    Given html string of <script src=""> tags, extracts list of static files stripping version info

    >>> _extract_urls(
    >>>     '<script src="/_dash-component-suites/dash/deps/polyfill@7.v2_0_0m1633432698.12.1.min.js"></script>\n<script src="/_dash-component-suites/dash/deps/react@16.v2_0_0m1633432698.14.0.min.js">'  # noqa
    >>> )
    /viewflow/js/contrib/dash/deps/polyfill@7.12.1.min.js
    """
    for url in re.findall('src="(.*)"', data):
        _, url = url.split("/_dash-component-suites/")
        start, end = url.rsplit(".v")
        extention = end.split(".", 1)[1]
        yield f"viewflow/js/contrib/{start}.{extention}"


class DashboardView(TemplateView):
    template_name = "viewflow/contrib/plotly.html"
    viewset = None

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            dash_scripts_urls=_extract_urls(
                self.viewset.dash_app._generate_scripts_html()
            ),
            dash_config_html=self.viewset.dash_app._generate_config_html(),
        )


@dash_view_permission_required
def layout_endpoint(request, viewset):
    dash_response = viewset.dash_app.serve_layout()
    return HttpResponse(dash_response.data, content_type="application/json")


@dash_view_permission_required
def dependencies_endpoint(request, viewset):
    return JsonResponse(viewset.dash_app._callback_list, safe=False)


@dash_view_permission_required
@csrf_exempt
@require_POST
def update_component_endpoint(request, viewset):
    try:
        request_body = json.loads(request.body.decode())

        output = request_body["output"]
        outputs_list = request_body["outputs"]

        inputs = request_body.get("inputs", [])
        state = request_body.get("state", [])

        callback_data = viewset.dash_app.callback_map[output]

    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse(
            {"code": 400, "message": f"Request body error: {e}"}, status=400
        )
    else:
        callback_args = [
            (
                [item.get("value") for item in items]
                if isinstance(items, list)
                else items.get("value")
            )
            for items in inputs + state
        ]

        callback_func = callback_data["callback"]
        result = callback_func(*callback_args, outputs_list=outputs_list)
        return HttpResponse(result, content_type="application/json")
