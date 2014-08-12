from django.contrib import admin
from viewflow.admin import ProcessAdmin
from . import models, flows


@admin.register(models.DynamicSplitProcess)
class DynamicSplitAdmin(ProcessAdmin):
    list_display = ['pk', 'created', 'get_status_display', 'participants',
                    'split_count', 'decisions_list']

    list_display_links = ['pk', 'created']

    def decisions_list(self, obj):
        return ', '.join(['No', 'Yes'][answer.decision] for answer in obj.decision_set.all())
