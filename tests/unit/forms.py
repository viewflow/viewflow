from django import forms


class AllElementsForm(forms.Form):
    text_input = forms.CharField(help_text="Sample text input")
    another_input = forms.CharField(show_hidden_initial=True)
