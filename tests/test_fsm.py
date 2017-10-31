import unittest
from viewflow.fsm import State, TransitionNotAllowed


class Test(unittest.TestCase):
    def test_base_transitions(self):
        base = Base()
        self.assertEqual('initial', base.state)

        self.assertTrue(base.prepare.can_proceed())
        self.assertEqual([Base.prepare], Base.state.get_available_transitions(base))
        base.prepare()
        self.assertEqual('prepared', base.state)

        self.assertTrue(base.start.can_proceed())
        self.assertEqual([Base.start], Base.state.get_available_transitions(base))
        base.start()
        self.assertEqual('started', base.state)

        self.assertTrue(base.done.can_proceed())
        self.assertEqual([Base.done], Base.state.get_available_transitions(base))
        base.done()
        self.assertEqual('done', base.state)

        self.assertFalse(base.done.can_proceed())
        self.assertEqual([], Base.state.get_available_transitions(base))
        self.assertRaises(TransitionNotAllowed, base.done)

    def test_child_transitions(self):
        child = Child()

        child.prepare()
        self.assertEqual('prepared', child.state)

        child.start()
        self.assertEqual('started', child.state)

        child.done()
        self.assertEqual('finalizing', child.state)

        child.shutdown()
        self.assertEqual('done', child.state)

        child.state = 'initial'
        self.assertEqual('initial', child.state)
        self.assertTrue(child.prepare.can_proceed())

    def test_subchild_transitions(self):
        sub_child = SubChild()

        self.assertEqual([SubChild.prepare], SubChild.state.get_available_transitions(sub_child))
        sub_child.prepare()
        self.assertEqual('prepared', sub_child.state)

        self.assertEqual([SubChild.start], SubChild.state.get_available_transitions(sub_child))
        sub_child.start()
        self.assertEqual('started', sub_child.state)

        self.assertEqual([SubChild.done], SubChild.state.get_available_transitions(sub_child))
        sub_child.done()
        self.assertEqual('finalizing', sub_child.state)

        sub_child.shutdown()
        self.assertEqual('done', sub_child.state)

    def test_subchild_withmixin_transitions(self):
        sub_child = SubChildWithMixin()
        self.assertTrue(sub_child.prepare.can_proceed())
        self.assertEqual([SubChildWithMixin.prepare], SubChildWithMixin.state.get_available_transitions(sub_child))
        sub_child.prepare()
        self.assertEqual('prepared', sub_child.state)

    def test_state_setter(self):
        state_setter = StateSetter()
        self.assertEqual('initial', state_setter.state)
        self.assertEqual('initial', state_setter.real_state)

        self.assertTrue(state_setter.done.can_proceed())
        state_setter.done()
        self.assertEqual('done', state_setter.state)
        self.assertEqual('done', state_setter.real_state)
        self.assertFalse(state_setter.done.can_proceed())

        state_setter.state = 'initial'
        self.assertEqual('initial', state_setter.real_state)
        self.assertTrue(state_setter.done.can_proceed())


class Base(object):
    state = State(default='initial')

    @state.transition(source='initial', target='prepared')
    def prepare(self):
        pass

    @state.transition(source='prepared', target='started')
    def start(self):
        pass

    @state.transition(source='started', target='done')
    def done(self):
        pass


class Child(Base):
    @Base.state.super()
    def start(self):
        super(Child, self).start.original()

    @Base.state.transition(source='started', target='finalizing')
    def done(self):
        pass

    @Base.state.transition(source='finalizing', target='done')
    def shutdown(self):
        pass


class SubChild(Child):
    pass


class Mixin(object):
    pass


class SubChildWithMixin(Mixin, Child):
    pass


class StateSetter(object):
    state = State()

    def __init__(self):
        self.real_state = 'initial'

    @state.setter()
    def set_state(self, value):
        self.real_state = value

    @state.getter()
    def get_state(self):
        return self.real_state

    @state.transition(source='initial', target='done')
    def done(self):
        pass
