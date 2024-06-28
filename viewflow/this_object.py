"""Forward-reference for class-body declarations"""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.
from typing import Any, Optional, Union


class ThisMethod:
    """
    Reference to a method for forward references in class bodies.

    This class is used to defer the resolution of a method reference until the
    class is fully constructed. This is particularly useful in workflow or state
    machine implementations where the flow references are declared before the
    methods are defined.
    """

    def __init__(self, propname: str, methodname: str):
        self._propname = propname
        self._methodname = methodname

    def resolve(self, instance) -> Any:
        """
        Resolve the method reference on the given instance.

        Args:
            instance (object): The instance on which to resolve the method.

        Returns:
            Any: The result of the resolved method call.

        Raises:
            AttributeError: If the property or method does not exist on the instance.
        """
        prop = getattr(instance, self._propname)
        method = getattr(instance, f"_this_{self._methodname}")
        return method(prop)


class ThisObject(object):
    """
    Helper for forward references to class attributes.

    This class is used to defer the resolution of an attribute reference until
    the class is fully constructed. This allows for the use of class attributes
    before they are defined.

    Attributes:
        name (str): The name of the attribute to resolve.
    """

    def __init__(self, name: str) -> None:  # noqa D102
        self.name = name

    def resolve(self, instance: object) -> Any:
        """
        Resolve the attribute reference on the given instance.

        Args:
            instance (object): The instance on which to resolve the attribute.

        Returns:
            Any: The resolved attribute.

        Raises:
            AttributeError: If the attribute does not exist on the instance.
        """
        return getattr(instance, self.name)

    # def __copy__(self):
    #     return super().__copy__()

    # def __deepcopy__(self, memo):
    #     return super().__deepcopy__(memo)

    def __getattr__(self, name):
        if name.startswith("__"):
            super().__getattr__(name)
        return ThisMethod(self.name, name)


class This:
    """
    Helper for building forward references to class attributes and methods.

    The rationale is the ability to specify references to the class attributes and
    methods before they are declared. `this` acts similarly to `self`, but for
    class-level forward references.
    """

    def resolve(self, instance: object, this_ref: Union[ThisObject, ThisMethod, Any]):
        """
        Resolve a forward reference on the given instance.

        Args:
            instance (object): The instance on which to resolve the reference.
            this_ref (Union[ThisObject, ThisMethod, Any]): The reference to resolve.

        Returns:
            Any: The resolved reference.

        Raises:
            AttributeError: If the reference cannot be resolved.
        """
        if isinstance(this_ref, (ThisObject, ThisMethod)):
            return this_ref.resolve(instance)
        else:
            return this_ref

    def __getattr__(self, name):
        return ThisObject(name)


# Instantiate a global `this` object for use in class definitions.
this = This()
