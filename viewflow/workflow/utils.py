class Act(object):
    """Shortcut to access activation data."""
    @property
    def process(self):
        """ Shortcut for lambda activation: activation.process...)"""
        class Lookup(object):
            def __getattribute__(self, name):
                return lambda activation: getattr(activation.process, name)
        return Lookup()

    @property
    def task(self):
        """ Shortcut for lambda activation: activation.task...)"""
        class Lookup(object):
            def __getattribute__(self, name):
                return lambda activation: getattr(activation.task, name)
        return Lookup()


act = Act()
