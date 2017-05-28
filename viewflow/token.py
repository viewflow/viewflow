from __future__ import unicode_literals

from itertools import count
from django.utils.deconstruct import deconstructible


@deconstructible
class Token(object):
    """
    Helper for tree-like flow token management.

    We follow basic strategy for flow split/join

    Flow starts with only one 'start' token,

    - each split adds split_pk and path id to following task 'start/3_4',
      and 'start/3_4/7_4' on one more split

    - each join removes corresponding split token addition, so 'start/3_4/7_4'
      becomes 'start/3_4'
    """

    def __init__(self, token):
        """
        Instantiate a new token.

        :param token: str
        """
        self.token = token

    def is_split_token(self):
        """True, if it is a token of parallel task."""
        return '/' in self.token

    def get_base_split_token(self):
        """Return token before last split happens."""
        return Token(self.token.rsplit('/', 1)[0])

    def get_common_split_prefix(self, join_token, task_pk):
        """Common prefix for tokens."""
        if self == join_token:
            return '{}/{}_'.format(self.token, task_pk)
        return '{}_'.format(self.token.rsplit('_', 1)[0])

    def __str__(self):
        return self.token

    def __eq__(self, other):
        if isinstance(other, Token):
            other_token = other.token
        elif isinstance(other, str):
            other_token = other
        else:
            return NotImplemented

        return self.token == other_token

    @classmethod
    def split_token_source(cls, prev_token, task_pk):
        """Span a set of uniq tokens with common prefix."""
        for n in count(1):
            yield Token("{}/{}_{}".format(prev_token, task_pk, n))
