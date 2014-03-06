from django import forms


class ActivationDataForm(forms.Form):
    started = forms.DateTimeField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('prefix', '_viewflow-activation')
        super(ActivationDataForm, self).__init__(*args, **kwargs)
