"""Tests for FSM descriptor and bound method customization hooks."""

from unittest import TestCase

from viewflow.fsm.base import (
    State,
    SuperTransitionDescriptor,
    TransitionBoundMethod,
    TransitionDescriptor,
)

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


class TrackingSuperBoundMethod(TransitionBoundMethod):
    """Custom bound method used for super() transitions."""

    wrapper_called = False

    class Wrapper(TransitionBoundMethod.Wrapper):
        """Wrapper that marks entry for super descriptor transitions."""

        def __enter__(self):
            """Set a flag and then enter the base wrapper context."""
            TrackingSuperBoundMethod.wrapper_called = True
            return super().__enter__()


class TrackingSuperDescriptor(SuperTransitionDescriptor):
    """Super transition descriptor that injects TrackingSuperBoundMethod."""

    bound_method_class = TrackingSuperBoundMethod


class TrackingStateWithSuper(TrackingState):
    """State that customizes descriptors for @transition and @super methods."""

    super_descriptor_class = TrackingSuperDescriptor


class PublicationWithCustomSuperDescriptor:
    """Base class that defines a removable transition."""

    state = TrackingStateWithSuper(ReviewState, default=ReviewState.NEW)

    @state.transition(source=State.ANY, target=ReviewState.REMOVED)
    def remove(self):
        """Transition to removed state."""
        pass


class GuestPublicationWithCustomSuperDescriptor(PublicationWithCustomSuperDescriptor):
    """Subclass overriding remove() via the @state.super decorator."""

    @PublicationWithCustomSuperDescriptor.state.super()
    def remove(self):
        """Delegate transition behavior to the parent original implementation."""
        super().remove.original()


class Test(TestCase):
    """Regression tests for customization extension points."""

    def setUp(self):
        """Reset instrumentation flags before each test case."""
        TrackingTransitionBoundMethod.wrapper_called = False
        TrackingSuperBoundMethod.wrapper_called = False

    def test_custom_bound_method_wrapper_is_used(self):
        """Custom bound method Wrapper is used for regular transition calls."""
        publication = PublicationWithCustomDescriptor()

        publication.publish()

        self.assertTrue(TrackingTransitionBoundMethod.wrapper_called)
        self.assertEqual(publication.state, ReviewState.PUBLISHED)

    def test_custom_super_descriptor_class_is_used(self):
        """State.super() uses configurable super_descriptor_class."""
        publication = GuestPublicationWithCustomSuperDescriptor()

        publication.remove()

        self.assertTrue(TrackingSuperBoundMethod.wrapper_called)
        self.assertEqual(publication.state, ReviewState.REMOVED)