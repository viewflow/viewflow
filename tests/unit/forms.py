from django import forms


class AllElementsForm(forms.Form):
    boolean_checkbox = forms.BooleanField()
    text_input = forms.CharField(help_text="Sample text input")
