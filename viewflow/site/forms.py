from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=250)
    password = forms.CharField(max_length=250, widget=forms.PasswordInput)
    remember = forms.BooleanField(default=False)
