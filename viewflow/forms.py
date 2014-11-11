from django import forms
from viewflow.models import Task


class ActivationDataForm(forms.ModelForm):
    started = forms.DateTimeField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('prefix', '_viewflow_activation')
        super(ActivationDataForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Task
        fields = ['started']
