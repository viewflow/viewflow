from django.shortcuts import render


def start(request, flow_task):
    if request.method == 'POST' and 'start' in request.POST:
        pass

    return render(request, 'onetwothree/start.html')


def one(request, flow_task, act_id):
    pass


def two(request, flow_task, act_id):
    pass


def three(request, flow_task, act_id):
    pass


def end(request, flow_task, act_id):
    pass
