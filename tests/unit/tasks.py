from viewflow.flow import flow_job


@flow_job()
def dummy_job(flow_task, task):
    pass
