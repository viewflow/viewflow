from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView
from django.shortcuts import redirect
from viewflow.flow import flow_start_view
from examples.shipment.models import Shipment

#from viewflow.flow import start
#
#
#class StartView(start.StartView):
#    def save_process(self):
#        self.process.created_by = self.request.us
#        return super(StartView, self).save_process()


class StartView(CreateView):
    template_name = 'shipment/flow/start.html'
    model = Shipment
    fields = ['goods_tag']

    def get_context_data(self, **kwargs):
        context = super(StartView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    def form_valid(self, form):
        self.object = form.save()
        self.activation.process.created_by = self.request.user
        self.activation.process.shipment = self.object
        self.activation.done()
        return redirect('viewflow:index')

    @flow_start_view()
    def dispatch(self, request, activation, **kwargs):
        self.activation = activation
        if not activation.flow_task.has_perm(request.user):
            raise PermissionDenied

        activation.prepare(request.POST or None)
        return super(StartView, self).dispatch(request, **kwargs)
