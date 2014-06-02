from django.contrib import admin, auth
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
    """
    List all of viewflow process
    """
    actions = None
    date_hierarchy = 'created'
    list_display = ['pk', 'created', 'flow_cls', 'get_status_display', 'participants']
    list_display_links = ['pk', 'created', 'flow_cls']
    list_filter = ['status']
    readonly_fields = ['flow_cls', 'status', 'finished']
    inlines = [TaskInline]

    def participants(self, obj):
        user_ids = obj.task_set.exclude(owner__isnull=True).values('owner')
        users = auth.get_user_model()._default_manager.filter(pk__in=user_ids).values_list('username')
        return ', '.join(user[0] for user in users)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    List all of viewflow tasks
    """
    actions = None
    date_hierarchy = 'created'
    list_display = ['pk', 'created', 'process', 'get_status_display',
                    'owner', 'owner_permission', 'token',
                    'started', 'finished']
    list_display_links = ['pk', 'created', 'process']
    list_filter = ['status']
    readonly_fields = ['process', 'flow_task', 'started', 'finished', 'previous', 'token']
