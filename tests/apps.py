import os
from django.apps import AppConfig


class TestsConfig(AppConfig):
    name = 'tests'
    path = os.path.dirname(os.path.abspath(__file__))

