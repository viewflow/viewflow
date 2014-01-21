from viewflow import flowsite
from onetwothree import models, flows


flowsite.register(models.StepProcess, flows.v1.StepFlow)
