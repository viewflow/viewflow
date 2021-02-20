/* eslint-env node */
const render = (ctx) => `from django.contrib import admin
from django.contrib.auth import admin as base

from . import forms, models


@admin.register(models.User)
class UserAdmin(base.UserAdmin):
    add_form = forms.UserCreationForm
    form = forms.UserChangeForm
    list_display = ('email', 'is_staff', 'is_active',)
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
`;

exports.default = render;