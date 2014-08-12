from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views import generic

from viewflow import flow


class FlowSiteMixin(object):
    flow_site = None

    def dispatch(self, request, *args, **kwargs):
        if 'flow_site' in kwargs:
            self.flow_site = kwargs['flow_site']
        if 'flow_cls' in kwargs:
            self.flow_cls = kwargs['flow_cls']

        return super(FlowSiteMixin, self).dispatch(request, *args, **kwargs)


class LoginView(FlowSiteMixin, generic.FormView):
    form_class = AuthenticationForm
    template_name = 'viewflow/login.html'

    def get_success_url(self):
        return reverse('viewflow_site:index', current_app=self.flow_site.app_name)

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_success_url())


class LogoutView(FlowSiteMixin, generic.View):
    def get_success_url(self):
        return reverse('viewflow_site:login', current_app=self.flow_site.app_name)

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return HttpResponseRedirect(self.get_success_url())


def processes_list_view(request, flow_site=None):
    """
    All process instances list available for current user
    """
    pass


def tasks_list_view(request, flow_site=None):
    """
    All tasks from all processes assigned to current user
    """
    pass


def queues_view(request, flow_site=None):
    """
    All unassigned tasks available for current user
    """
    pass


class ProcessListView(FlowSiteMixin, generic.ListView):
    paginate_by = 3
    paginate_orphans = 0
    context_object_name = 'process_list'

    def get_template_names(self):
        return ('{}/flow/index.html'.format(self.flow_cls._meta.app_label),
                'viewflow/flow/index.html')

    def available_start_actions(self):
        """
        Return list of start flow actions data available for the user
        """

        actions = []
        for node in self.flow_cls._meta.nodes():
            if isinstance(node, flow.Start) and node.has_perm(self.request.user):
                node_url = reverse(
                    'viewflow:{}'.format(node.name),
                    current_app=self.flow_cls._meta.namespace)

                actions.append((node_url, node.name))

        return actions

    def get_context_data(self, **kwargs):
        context = super(ProcessListView, self).get_context_data(**kwargs)
        context['start_actions'] = self.available_start_actions()
        context['flow_cls'] = self.flow_cls
        return context

    def get_queryset(self):
        return self.flow_cls.process_cls.objects \
            .filter(flow_cls=self.flow_cls) \
            .order_by('-created')


def process_detail_view(request, flow_site=None, flow_cls=None):
    """
    Details for process
    """


def task_list_view(request, flow_site=None, flow_cls=None):
    """
    List of specific Flow tasks assigned to current user
    """


def queue_view(request, flow_site=None, flow_cls=None):
    """
    List of specific Flow unassigned tasks available for current user
    """
