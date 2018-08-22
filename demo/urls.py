from django.conf.urls import include, url
from django.contrib.auth import views as auth
from django.views import generic

from material import frontend
from material.frontend.apps import ModuleMixin
from material.frontend.registry import modules


class Demo(ModuleMixin):
    """
    Home page module
    """
    order = 1
    label = 'Introduction'
    icon = '<i class="material-icons">account_balance</i>'

    @property
    def urls(self):
        index_view = generic.TemplateView.as_view(template_name='demo/index.html')

        return frontend.ModuleURLResolver(
            '^', [url('^$', index_view, name="index")],
            module=self, app_name='demo', namespace='demo')

    def index_url(self):
        return '/'

    def installed(self):
        return True


modules.register(Demo())


from material.frontend import urls as frontend_urls  # NOQA

urlpatterns = [
    url(r'^accounts/login/$', auth.LoginView.as_view(), name='login'),
    url(r'^accounts/logout/$', auth.LogoutView.as_view(), name='logout'),
    url(r'^', include('demo.website')),
    url(r'', include(frontend_urls)),
]
