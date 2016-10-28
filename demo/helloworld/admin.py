from django.contrib import admin
from viewflow.admin import ProcessAdmin

from . import models


class HelloWorldProcessAdmin(ProcessAdmin):
    icon = '<i class="material-icons">flag</i>'
    list_display = ['pk', 'created', 'status', 'participants',
                    'text', 'approved']
    list_display_links = ['pk', 'created']


admin.site.register(models.HelloWorldProcess, HelloWorldProcessAdmin)
