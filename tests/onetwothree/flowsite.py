from viewflow import flowsite
from onetwothree import models
from onetwothree.flows import v1


flowsite.register(models.StepProcess, v1.StepFlow)
