import functools
from django.test import TestCase
from viewflow import this


class Review(object):
    approver = 'Will Smith'
    publisher = 'John Doe'

    def approve(self):
        return 'approve'

    def publish(self):
        return 'publish'

    def _this_owner(self, transition):
        if transition == self.approve:
            return self.approver
        elif transition == self.publish:
            return self.publisher
        else:
            raise ValueError(f"Can't find owner for {transition}")

    def _this_call(self, transition):
        def call_transition(self, transition):
            return transition()
        return functools.partial(call_transition, self, transition)



class Test(TestCase):
    def test_this_refs_data(self):
        self.assertEqual(this.some_name.name, 'some_name')
        self.assertEqual(this.another_some_name.name, 'another_some_name')

    def test_this_ref_resolve(self):
        review = Review()

        approve = this.approve.resolve(review)
        self.assertEqual(approve, review.approve)
        self.assertEqual(Review.approver, this.approve.owner.resolve(review))
        self.assertEqual(this.approve.call.resolve(review)(), 'approve')

        publish = this.publish.resolve(review)
        self.assertEqual(publish, review.publish)
        self.assertEqual(Review.publisher, this.publish.owner.resolve(review))
        self.assertEqual(this.publish.call.resolve(review)(), 'publish')
