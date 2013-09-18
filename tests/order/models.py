from viewflow.models import Process


class CustomerOrderProcess(Process):
    pass


class LowStockProcess(Process):
    pass


class ProcurementProcess(Process):
    def fast_delivarable(self):
        raise NotImplementedError

    def late_delivarable(self):
        raise NotImplementedError
