from django.contrib import admin
from viewflow.models import Process, Task


class TaskInline(admin.TabularInline):
    model = Task
    fields = ['flow_task', 'flow_task_type', 'status',
              'owner', 'owner_permission', 'token',
              'started', 'finished']
    readonly_fields = ['flow_task', 'flow_task_type', 'status',
                       'token', 'started', 'finished']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['pk', 'flow_cls', 'get_status_display']
    readonly_fields = ['flow_cls', 'status', 'finished']
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
