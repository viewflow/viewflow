/* eslint-env node */
const render = (ctx) => `from django import forms
from django.contrib.auth import forms as base

from .models import User


class UserCreationForm(base.UserCreationForm):
    class Meta(base.UserCreationForm.Meta):
        model = User
        fields = ('email',)


class UserChangeForm(base.UserChangeForm):
    class Meta(base.UserChangeForm.Meta):
        model = User
        fields = ('email',)
`;

exports.default = render;