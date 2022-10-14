# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial licence defined in file 'COMM_LICENSE',
# which is part of this source code package.

from django import forms
from viewflow.utils import viewprop
from viewflow.forms import Span


def _collect_elements(parent, container=None):
    if container is None:
        container = []

    if hasattr(parent, 'children'):
        for element in parent.children:
            _collect_elements(element, container=container)

    if isinstance(parent, Span):
        container.append(parent.field_name)

    return container


class FormLayoutMixin(object):
    """
    Mixin for FormView to infer View.fields definition from form Layout.
    """
    form_class = None

    @viewprop
    def layout(self):
        if self.form_class is None and hasattr(self.form_class, 'layout'):
            return self.form_class.layout

    @viewprop
    def fields(self):
        if self.form_class is None:
            if self.layout is not None:
                return _collect_elements(self.layout)
            else:
                return '__all__'


class Action(object):
    def __init__(self, name, url=None, viewname=None, icon=None):
        assert url or viewname
        self.name = name
        self.url = url
        self.viewname = viewname
        self.icon = icon


class BulkActionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        model = kwargs.pop('model')
        super().__init__(*args, **kwargs)

        self.fields['pk'] = forms.ModelMultipleChoiceField(
            queryset=model._default_manager.all(),
            widget=forms.MultipleHiddenInput,
            required=False
        )

        self.fields['select_all'] = forms.CharField(
            widget=forms.HiddenInput,
            required=False
        )
