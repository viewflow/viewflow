from django.dispatch import Signal

flow_started = Signal(providing_args=["process", "task"])
flow_finished = Signal(providing_args=["process", "task"])

task_started = Signal(providing_args=["process", "task"])
task_failed = Signal(providing_args=["process", "task", "exception", "traceback"])
task_finished = Signal(providing_args=["process", "task"])
