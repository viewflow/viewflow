from viewflow import flowsite
from shipment import models, flows

flowsite.register(models.ShipmentProcess, flows.ShipmentFlow)
