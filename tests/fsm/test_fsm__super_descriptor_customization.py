"""Tests for customizable super transition descriptor classes."""

from unittest import TestCase

from viewflow.fsm.base import (
    State,
    SuperTransitionDescriptor,
    TransitionBoundMethod,
    TransitionDescriptor,
)

from .test_fsm__basics import ReviewState


class TrackingTransitionBoundMethod(TransitionBoundMethod):
    """Base custom bound method used by the custom state class."""


class TrackingTransitionDescriptor(TransitionDescriptor):
    """Descriptor used by the custom state implementation."""

    bound_method_class = TrackingTransitionBoundMethod


class TrackingState(State):
    """State that uses the custom regular transition descriptor."""

    descriptor_class = TrackingTransitionDescriptor


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
    """Regression tests for configurable super transition descriptors."""

    def setUp(self):
        """Reset instrumentation flags before each test case."""
        TrackingSuperBoundMethod.wrapper_called = False

    def test_custom_super_descriptor_class_is_used(self):
        """State.super() uses configurable super_descriptor_class."""
        publication = GuestPublicationWithCustomSuperDescriptor()

        publication.remove()

        self.assertTrue(TrackingSuperBoundMethod.wrapper_called)
        self.assertEqual(publication.state, ReviewState.REMOVED)