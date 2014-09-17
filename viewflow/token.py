from itertools import count
from .compat import deconstructible


@deconstructible
class Token(object):
    """
    Hellper for tree-like flow token management

    We follow basic strategy for flow split/join

    Flow starts with only one 'start' token,

    - each split adds split_pk and path id to following task 'start/3_4',
      and 'start/3_4/7_4' on one more split

    - each join removes corresponding split token addition, so 'start/3_4/7_4'
      becomes 'start/3_4'
    """
    def __init__(self, token):
        self.token = token

    def is_split_token(self):
        return '/' in self.token

    def get_base_split_token(self):
        """
        Returns token before split happens
        """
        return Token(self.token.rsplit('/', 1)[0])

    def get_common_split_prefix(self):
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
        for n in count(1):
            yield "{}/{}_{}".format(prev_token, task_pk, n)
