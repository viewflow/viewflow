from itertools import islice
from django.test import TestCase
from viewflow.token import Token


class Test(TestCase):
    def test_token_equals_succeed(self):
        token1 = Token('start/1')
        token2 = Token('start/1')
        self.assertEqual(token1, token2)

    def test_token_api(self):
        token = Token('start/1_2/3_4')

        self.assertTrue(token.is_split_token())
        self.assertEqual(token.get_base_split_token(), 'start/1_2')
        self.assertEqual(token.get_common_split_prefix(), 'start/1_2/3_')

    def test_split_token_source_generator(self):
        prev_token = Token('start/1_2/3_4')
        source = Token.split_token_source(prev_token, task_pk=5)
        tokens = list(islice(source, 5))

        self.assertEqual(set([Token(token).get_common_split_prefix() for token in tokens]),
                         set(['start/1_2/3_4/5_']))
