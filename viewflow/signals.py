from django.dispatch import Signal

# providing_args=["process", "task"]
flow_started = Signal()
# providing_args=["process", "task"]
flow_finished = Signal()

# providing_args=["process", "task"]
task_started = Signal()
# providing_args=["process", "task", "exception", "traceback"]
task_failed = Signal()
# providing_args=["process", "task"]
task_finished = Signal()
