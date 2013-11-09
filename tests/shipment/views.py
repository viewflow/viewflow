from django.shortcuts import get_object_or_404, render
from viewflow.models import Activation


def shipment_type(request, act_id):
    """
    Decide if normal post or special shipment
    """
    activation = get_object_or_404(Activation, pk=act_id)

    if request.method == 'POST':
        activation.done(save=True)
        return activation.redirect_to_next()

    return render(request, 'shipment/shipment_type.html', {
        'activation': activation
    })


def package_goods(request, act_id):
    """
    Package goods
    """
    raise NotImplementedError


def check_insurance(request, act_id):
    """
    Check if extra insurance is necessary
    """
    raise NotImplementedError


def request_quotes(request, act_id):
    """
    Check if extra insurance is necessary
    """
    raise NotImplementedError


def take_extra_insurance(request, act_id):
    """
    Take out extra insurance
    """
    raise NotImplementedError


def fill_post_label(request, act_id):
    """
    Fill in a Post label
    """
    raise NotImplementedError


def assign_carrier(request, act_id):
    """
    Assign a carrier & prepare paperwork
    """
    raise NotImplementedError


def move_package(request, act_id):
    """
    Assign a carrier & prepare paperwork
    """
    raise NotImplementedError
