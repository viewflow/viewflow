from django.dispatch import Signal

test_start_flow = Signal(providing_args=["message"])
test_done_flow_task = Signal(providing_args=["message"])
