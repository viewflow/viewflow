from .base import ViewSite
from .viewform import (Layout, Row, Column, Fieldset, Inline,        # NOQA
                       Field, Span2, Span3, Span4, Span5, Span6,
                       Span7, Span8, Span9, Span10, Span11, Span12,
                       LayoutMixin)


viewsite = ViewSite()


def autodiscover():
    from ..compat import autodiscover_modules
    autodiscover_modules('flows', register_to=viewsite)


default_app_config = 'viewflow.site.apps.ViewSiteConfig'
