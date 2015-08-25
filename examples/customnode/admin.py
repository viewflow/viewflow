from django.contrib import admin
from viewflow.admin import ProcessAdmin
from . import models


class DynamicSplitAdmin(ProcessAdmin):
    list_display = ['pk', 'created', 'status', 'participants',
                    'split_count', 'decisions_list']

    list_display_links = ['pk', 'created']

    def decisions_list(self, obj):
        return ', '.join(['No', 'Yes'][answer.decision] for answer in obj.decision_set.all())


admin.site.register(models.DynamicSplitProcess, DynamicSplitAdmin)
