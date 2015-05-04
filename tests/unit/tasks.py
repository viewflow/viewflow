from viewflow.flow import flow_job, flow_signal, flow_func


@flow_job()
def dummy_job(flow_task, task):
    pass


def start_process(activation, **kwargs):
    activation.prepare()
    activation.done()


@flow_signal(lambda flow_task, sender: sender.get_task(flow_task))
def do_signal_task(activation, **kwargs):
    activation.prepare()
    activation.done()


def do_handler_task(activation):
    pass


@flow_func(lambda flow_task, process: process.get_task(flow_task))
def do_func_task(activation, process):
    activation.prepare()
    activation.done()
