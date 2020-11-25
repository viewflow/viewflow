"""Forward-reference for class-body declarations"""


class ThisMethod(object):
    """Reference to a method"""
    def __init__(self, propname, methodname):
        self._propname = propname
        self._methodname = methodname

    def resolve(self, instance):
        # TODO meaningfull exception
        prop = getattr(instance, self._propname)
        method = getattr(instance, f'_this_{self._methodname}')
        return method(prop)


class ThisObject(object):
    """Helper for forward references"""

    def __init__(self, name):  # noqa D102
        self.name = name

    def resolve(self, instance):
        # TODO meaningfull exception
        return getattr(instance, self.name)

    def __getattr__(self, name):
        return ThisMethod(self.name, name)


class This(object):
    """Helper for building forward references.

    The rationale is ability to specify references to the class
    attributes and methods before they are declared.

    `this` is like a `self` but for the class body.
    """
    def resolve(self, instance, this_ref):
        if isinstance(this_ref, (ThisObject, ThisMethod)):
            return this_ref.resolve(instance)
        else:
            return this_ref

    def __getattr__(self, name):
        return ThisObject(name)


this = This()
