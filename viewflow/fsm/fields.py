"""Backward-compatible ``FSMField``, ported from django-fsm.

Reuses the ``Transition``/``TransitionDescriptor``/``TransitionBoundMethod``
core in :mod:`viewflow.fsm.base` unchanged -- ``FSMField`` only supplies a
storage location (the model instance's own attribute slot) instead of the
``State.propname``-mangled slot a plain :class:`~viewflow.fsm.State` uses,
so a value survives Django's normal field machinery (``pre_save``,
filtering, serialization) as-is.
"""

from __future__ import annotations

from typing import Any, List, Optional

from django.db import models

from .base import DEFAULT, State, StateValue, TransitionNotAllowed
from .typing import Condition, Permission


class NonInitialStateOnCreate(TransitionNotAllowed):
    """Raised creating a new row through ``FSMField(enforce_initial=True)``
    with a value other than the field's declared default.

    :ivar field: the :class:`FSMField` involved.
    :ivar value: the rejected value.
    """

    def __init__(self, field: "FSMField", value: Any):
        self.field = field
        self.value = value
        super().__init__(
            f"Cannot create {field.model.__name__}.{field.name} as {value!r};"
            f" new rows must start at the declared initial state"
            f" {field.get_default()!r}"
        )


class _FSMFieldState(State):
    """A ``State`` whose storage is the owning field's own attribute slot on
    the model instance, instead of a plain ``State``'s private, name-mangled
    ``propname`` -- so the value lives exactly where Django's own field
    machinery expects it (``pre_save``, ``filter()``, serialization).

    Bound to the field, not a fixed attribute name, since ``FSMField.attname``
    and ``FSMField.get_default()`` are only valid after ``contribute_to_class``
    runs -- which happens *after* the class body's ``@field.transition(...)``
    decorators already needed a working ``State`` to register against.
    """

    def __init__(self, field: "FSMField"):
        super().__init__(states=None, default=None)
        self._field = field

    @property
    def propname(self) -> str:
        return self._field.attname

    def get(self, instance: object) -> Any:
        if self.propname in instance.__dict__:
            return instance.__dict__[self.propname]
        return self._field.get_default()

    def set(self, instance: object, value: StateValue) -> None:
        instance.__dict__[self.propname] = value


class FSMField(models.CharField):
    """A ``CharField`` whose value only changes through ``@transition``-guarded
    methods -- a same-column drop-in for django-fsm's ``FSMField``.

    ``protected`` (default ``False``, matching django-fsm): once ``True``,
    direct assignment (``instance.state = x``) raises ``AttributeError``
    after the instance's first value is set (by ``Model.__init__``/loading
    from the database) -- transitions still work, since they write through
    ``State.set()``, not attribute assignment. Note this also blocks a
    plain ``instance.refresh_from_db()`` re-assigning the field; there is no
    workaround for that yet, so only opt in if you don't rely on it.

    ``enforce_initial`` (default ``False``): once ``True``, raises
    ``NonInitialStateOnCreate`` from ``pre_save`` if a *new* row (``add``)
    would be inserted with a value other than the field's ``default`` --
    closing the gap where ``Model.objects.create(state=DONE)`` bypasses
    every transition. Does not cover ``bulk_create()`` or raw SQL, which
    skip ``pre_save`` entirely.

    Both default to ``False`` so porting from django-fsm is a same-behavior
    import swap; opt into either (or both) for viewflow's stricter
    guarantees once ported code is running.
    """

    def __init__(
        self,
        *args: Any,
        protected: bool = False,
        enforce_initial: bool = False,
        **kwargs: Any,
    ):
        self.protected = protected
        self.enforce_initial = enforce_initial
        self._state = _FSMFieldState(self)
        super().__init__(*args, **kwargs)

    def contribute_to_class(
        self, cls: type, name: str, private_only: bool = False
    ) -> None:
        super().contribute_to_class(cls, name, private_only=private_only)
        setattr(cls, self.attname, self)

    def __get__(self, instance: Optional[object], owner: Optional[type] = None) -> Any:
        if instance is None:
            return self
        return self._state.get(instance)

    def __set__(self, instance: object, value: StateValue) -> None:
        if self.protected and self.attname in instance.__dict__:
            raise AttributeError(
                f"Direct assignment to '{self.attname}' is not allowed;"
                " use a transition method instead"
            )
        instance.__dict__[self.attname] = value

    def pre_save(self, model_instance: models.Model, add: bool) -> Any:
        value = super().pre_save(model_instance, add)
        if self.enforce_initial and add and value != self.get_default():
            raise NonInitialStateOnCreate(self, value)
        return value

    def transition(
        self,
        source: StateValue,
        target: Optional[StateValue] = DEFAULT,
        label: Optional[str] = None,
        conditions: Optional[List[Condition]] = None,
        permission: Optional[Permission] = DEFAULT,
        custom: Optional[Any] = None,
    ) -> Any:
        return self._state.transition(
            source,
            target,
            label=label,
            conditions=conditions,
            permission=permission,
            custom=custom,
        )


def transition(
    field: FSMField,
    source: StateValue,
    target: Optional[StateValue] = DEFAULT,
    **kwargs: Any,
) -> Any:
    """django-fsm-compatible decorator: ``@transition(field=state, source=..., target=...)``.

    Thin wrapper over ``field.transition(...)`` for code ported from
    django-fsm, where the field object is passed explicitly rather than
    calling ``.transition()`` on it directly.
    """
    return field.transition(source, target, **kwargs)
