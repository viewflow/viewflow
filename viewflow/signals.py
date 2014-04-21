from django.dispatch import Signal

flow_started = Signal(providing_args=["process", "task"])
flow_finished = Signal(providing_args=["process", "task"])
task_started = Signal(providing_args=["process", "task"])
task_finished = Signal(providing_args=["process", "task"])
task_prepared = Signal(providing_args=["process", "task"])
