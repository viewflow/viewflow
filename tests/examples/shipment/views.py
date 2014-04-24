from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView
from django.shortcuts import redirect, render
from viewflow.flow import flow_start_view
from examples.shipment.models import Shipment

#from viewflow.flow import start
#
#
#class StartView(start.StartView):
#    def save_process(self):
#        self.process.created_by = self.request.us
#        return super(StartView, self).save_process()


@flow_start_view()
def start_view(request, activation):
    form_cls = None

    if not activation.flow_task.has_perm(request.user):
        raise PermissionDenied

    activation.prepare(request.POST or None)
    form = form_cls(request.POST or None)

    if form.is_valie():
        shipment = form.save()
        activation.process.created_by = request.user
        activation.process.shipment = shipment
        activation.done()
        return redirect('viewflow:index')

    return render(request, 'shipment/flow/start.html', {
        'form': form,
        'activation': activation
    })


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
