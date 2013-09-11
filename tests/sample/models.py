from viewflow.models import Process


class ShipmentProcess(Process):
    def is_normal_post():
        raise NotImplementedError

    def need_extra_insurance():
        raise NotImplementedError

