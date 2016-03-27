class FlowFunc(object):
    def get_task(self, flow_task, *func_args, **func_kwars):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class Receiver(object):

    """
    Flow signal receiver that gets the signaled task form the kwargs.

    Subclasses must implement :method:`.get_task` and :method:`.__call__`.

    Example::

        @flow_signal()
        class MyReceiver(Receiver):
            def get_task(self, flow_task, **signal_kwargs):
                return kwargs['process'].get_task(flow_task)

            def __call__(self, activation, **signal_kwargs):
                activation.prepare()
                activation.done()

    .. note::

        In this example your signal will need to be send
        with ``process`` as a kwarg.

    """

    def get_task(self, flow_task, **signal_kwargs):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        raise NotImplementedError
