import os

from celery import shared_task
from viewflow.flow import flow_job


@shared_task(bind=True)
@flow_job()
def send_hello_world_request(self, activation):
    with open(os.devnull, "w") as world:
        world.write(activation.process.text)
