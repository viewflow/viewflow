from django import forms
from viewflow.models import Task


class ActivationDataForm(forms.ModelForm):
    """Default form to track activation data."""

    started = forms.DateTimeField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):  # noqa D102
        kwargs.setdefault('prefix', '_viewflow_activation')
        super(ActivationDataForm, self).__init__(*args, **kwargs)

    class Meta:  # noqa D101
        model = Task
        fields = ['started']
