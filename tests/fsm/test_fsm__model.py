from django.db import models
from django.test import TestCase
from viewflow import fsm
from .test_fsm__basics import ReviewState


class Report(models.Model):
    text = models.TextField()
    stage = models.CharField(max_length=150)


class ReportReview(object):
    stage = fsm.State(ReviewState, default=ReviewState.NEW)

    def __init__(self, report):
        self.report = report

    @stage.setter()
    def _set_report_stage(self, value):
        self.report.stage = value

    @stage.getter()
    def _get_report_stage(self):
        return self.report.stage

    @stage.on_success()
    def _on_transition_success(self, descriptor, source, target):
        self.report.save()

    @stage.transition(
        source=ReviewState.NEW,
        target=ReviewState.PUBLISHED
    )
    def publish(self):
        pass

    @stage.transition(
        source=fsm.State.ANY,
        target=ReviewState.REMOVED
    )
    def remove(self):
        pass


class Test(TestCase):
    def test_default_state_of_new_object(self):
        report = Report(text="test")
        review = ReportReview(report)
        self.assertEqual(review.stage, ReviewState.NEW)

    def test_state_of_existing_object(self):
        report = Report.objects.create(stage=ReviewState.PUBLISHED, text="test")
        review = ReportReview(report)
        self.assertEqual(review.stage, ReviewState.PUBLISHED)

    def test_state_success_called(self):
        report = Report(text="test")
        review = ReportReview(report)
        review.publish()

        self.assertEqual(review.stage, ReviewState.PUBLISHED)
        self.assertEqual(report.stage, ReviewState.PUBLISHED)
        self.assertTrue(report.pk is not None)
