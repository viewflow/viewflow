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


class IntStageReport(models.Model):
    stage = models.IntegerField(null=True)


class IntStageReview(object):
    # default is deliberately non-zero, so a falsy-but-legitimate state
    # (0) is distinguishable from "no getter value yet".
    stage = fsm.State(int, default=1)

    def __init__(self, report):
        self.report = report

    @stage.setter()
    def _set_stage(self, value):
        self.report.stage = value

    @stage.getter()
    def _get_stage(self):
        return self.report.stage

    @stage.transition(source=0, target=1)
    def advance(self):
        pass


class Test(TestCase):
    def test_default_state_of_new_object(self):
        report = Report(text="test")
        review = ReportReview(report)
        self.assertEqual(review.stage, ReviewState.NEW)

    def test_zero_is_a_legitimate_state_not_replaced_by_default(self):
        # State.get() replaced *any* falsy getter value (0, False, "")
        # with the default, not just "no value yet". An IntegerField-backed
        # state of 0 was silently promoted to the (non-zero) default.
        report = IntStageReport(stage=0)
        review = IntStageReview(report)
        self.assertEqual(review.stage, 0)

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
