import pickle
from unittest import TestCase

from viewflow import fsm


class PicklableTaskA(object):
    status = fsm.State(["new", "done"], default="new")

    @status.transition(source="new", target="done")
    def complete(self):
        pass


class PicklableTaskB(object):
    # A second, independently constructed State() descriptor declared
    # on the same attribute name -- exactly what a fresh module import
    # in a different process produces for the *same* source class.
    status = fsm.State(["new", "done"], default="new")


class Test(TestCase):
    def test_propname_is_stable_across_independently_constructed_descriptors(self):
        # propname derived the storage attribute from id(self) -- the
        # State descriptor object's own memory address, which is only
        # stable within a single running process. Two independently
        # constructed State() descriptors declared on the same
        # attribute name (as happens when a module is freshly
        # re-imported in a different process) produced different
        # propnames, since id() differs per object.
        self.assertEqual(
            PicklableTaskA.status.propname, PicklableTaskB.status.propname
        )

    def test_pickled_state_survives_a_fresh_descriptor_instance(self):
        # A plain-object flow pickled to a session/cache and unpickled
        # in a different process reverted to the default state: the
        # unpickled instance's __dict__ still had the *old* process's
        # propname key, but the *new* process's State object (a fresh
        # instance with a different id()) looked up a different key,
        # missed, and fell back to the default.
        task = PicklableTaskA()
        task.complete()
        self.assertEqual(task.status, "done")

        data = pickle.dumps(task)
        # Force-unpickle as PicklableTaskB, whose `status` descriptor
        # is a completely separate State() object, standing in for the
        # class as it would be freshly re-defined in another process.
        data = data.replace(b"PicklableTaskA", b"PicklableTaskB")

        restored = pickle.loads(data)
        self.assertEqual(restored.status, "done")
