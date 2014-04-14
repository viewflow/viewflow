import os

from viewflow.flow import flow_job
from examples.helloworld.models import HelloWorldProcess

"""
@flow_job()
def send_hello_world_request(flow_task, task):
    process = HelloWorldProcess.objects.get(task=task)

    with open(os.devnull, "w") as world:
        world.write(process.text)
"""
