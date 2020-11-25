"""Tests for @transition(conditions=...) parameter."""

from django.test import TestCase
from viewflow import this
from viewflow.fsm import State, TransitionNotAllowed
from .test_fsm__basics import ReviewState


class _Publication(object):
    stage = State(
        ReviewState,
        default=ReviewState.NEW
    )

    def __init__(self, text):
        self.text = text

    @stage.transition(
        source=ReviewState.NEW,
        target=ReviewState.PUBLISHED,
        conditions=[this.is_long]
    )
    def publish(self):
        pass

    def is_long(self):
        return State.CONDITION(
            len(self.text) > 1000,
            unmet="Review is too short"
        )


class _Test(TestCase):
    def test_conditions_met(self):
        publication = _Publication('test' * 251)
        publication.publish()

    def test_unmet_conditions_raises_exception(self):
        publication = _Publication('test' * 249)
        with self.assertRaises(TransitionNotAllowed):
            publication.publish()

