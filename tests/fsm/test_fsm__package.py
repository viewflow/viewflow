"""The historical Viewflow paths share the standalone FSM implementation."""

import importlib
import importlib.util

from django.test import SimpleTestCase
from django.utils.module_loading import import_string

import django_fsm
from django_fsm import this
from django_fsm.this_object import ThisObject
from django_fsm.utils import DEFAULT, MARKER
from viewflow import fsm
from viewflow import this as viewflow_this
from viewflow.this_object import ThisObject as ViewflowThisObject
from viewflow.utils import DEFAULT as VIEWFLOW_DEFAULT, MARKER as ViewflowMarker


class PackageCompatibilityTests(SimpleTestCase):
    def test_core_exports_are_identical(self):
        for name in django_fsm.__all__:
            with self.subTest(name=name):
                self.assertIs(getattr(fsm, name), getattr(django_fsm, name))

    def test_forward_references_and_sentinels_are_shared(self):
        self.assertIs(viewflow_this, this)
        self.assertIs(ViewflowThisObject, ThisObject)
        self.assertIs(VIEWFLOW_DEFAULT, DEFAULT)
        self.assertIs(ViewflowMarker, MARKER)

    def test_submodules_are_aliases(self):
        for name in (
            "base",
            "fields",
            "typing",
            "signals",
            "chart",
            "admin",
            "views",
            "viewset",
            "rest",
        ):
            with self.subTest(module=name):
                # rest.py is PRO-only and is not shipped to the OSS tree.
                if (
                    name == "rest"
                    and importlib.util.find_spec("viewflow.fsm.rest") is None
                ):
                    continue
                self.assertIs(
                    importlib.import_module(f"viewflow.fsm.{name}"),
                    importlib.import_module(f"django_fsm.{name}"),
                )

    def test_old_migration_import_paths_still_resolve(self):
        for name in ("FSMField", "FSMIntegerField", "FSMKeyField"):
            with self.subTest(name=name):
                self.assertIs(
                    import_string(f"viewflow.fsm.fields.{name}"),
                    getattr(django_fsm, name),
                )
                self.assertIs(
                    import_string(f"django_fsm.{name}"), getattr(django_fsm, name)
                )
