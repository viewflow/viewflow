from django.core.management.base import BaseCommand

from viewflow.workflow.timers import (
    fire_due_conditions,
    fire_due_start_timers,
    fire_due_timers,
)


class Command(BaseCommand):
    help = "Fire due database-backed workflow timers and scheduled process starts"

    def handle(self, **options):
        fired = fire_due_timers()
        started = fire_due_start_timers()
        conditions = fire_due_conditions()
        self.stdout.write(
            f"{fired} timer(s) fired, {started} process(es) started, "
            f"{conditions} condition(s) fired"
        )
