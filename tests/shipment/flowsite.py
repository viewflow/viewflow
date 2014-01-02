from viewflow import flowsite
from shipment import models, flow

flowsite.register(models.ShipmentProcess, flow.ShipmentFlow)
