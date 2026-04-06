"""Tests for customizable regular transition bound method wrappers."""

from unittest import TestCase

from viewflow.fsm.base import State, TransitionBoundMethod, TransitionDescriptor

from .test_fsm__basics import ReviewState


class TrackingTransitionBoundMethod(TransitionBoundMethod):
    """Custom bound method that records Wrapper context entry."""

    wrapper_called = False

    class Wrapper(TransitionBoundMethod.Wrapper):
        """Wrapper that marks when transition execution enters the context."""

        def __enter__(self):
            """Set a flag and delegate to the base context manager."""
            TrackingTransitionBoundMethod.wrapper_called = True
            return super().__enter__()


class TrackingTransitionDescriptor(TransitionDescriptor):
    """Descriptor that injects TrackingTransitionBoundMethod for binding."""

    bound_method_class = TrackingTransitionBoundMethod


class TrackingState(State):
    """State that uses TrackingTransitionDescriptor for @transition methods."""

    descriptor_class = TrackingTransitionDescriptor


class PublicationWithCustomDescriptor:
    """Flow-like object using a custom transition descriptor class."""

    state = TrackingState(ReviewState, default=ReviewState.NEW)

    @state.transition(source=ReviewState.NEW, target=ReviewState.PUBLISHED)
    def publish(self):
        """Transition to published state."""
        pass


class Test(TestCase):
    """Regression tests for regular transition customization."""

    def setUp(self):
        """Reset instrumentation flags before each test case."""
        TrackingTransitionBoundMethod.wrapper_called = False

    def test_custom_bound_method_wrapper_is_used(self):
        """Custom bound method Wrapper is used for regular transition calls."""
        publication = PublicationWithCustomDescriptor()

        publication.publish()

        self.assertTrue(TrackingTransitionBoundMethod.wrapper_called)
        self.assertEqual(publication.state, ReviewState.PUBLISHED)