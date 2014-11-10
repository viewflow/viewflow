from viewflow import flow
from viewflow.base import Flow, this


class NoTaskFlow(Flow):
    start = flow.Start().Next(this.end)
    end = flow.End()


class TaskErrorFlow(Flow):
    start = flow.Start().Next(this.end)
    end = flow.End()


class GateErrorFlow(Flow):
    start = flow.Start().Next(this.end)
    end = flow.End()
