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


class ProcessAdmin(admin.ModelAdmin):
    """
    List all of viewflow process
    """
    actions = None
    date_hierarchy = 'created'
    list_display = ['pk', 'created', 'flow_cls', 'status', 'participants']
    list_display_links = ['pk', 'created', 'flow_cls']
    list_filter = ['status']
    readonly_fields = ['flow_cls', 'status', 'finished']
    # inlines = [TaskInline]

    def participants(self, obj):
        user_ids = obj.task_set.exclude(owner__isnull=True).values('owner')
        users = auth.get_user_model()._default_manager.filter(pk__in=user_ids).values_list('username')
        return ', '.join(user[0] for user in users)


class TaskAdmin(admin.ModelAdmin):
    """
    List all of viewflow tasks
    """
    actions = None
    date_hierarchy = 'created'
    list_display = ['pk', 'created', 'process', 'status',
                    'owner', 'owner_permission', 'token',
                    'started', 'finished']
    list_display_links = ['pk', 'created', 'process']
    list_filter = ['status']
    readonly_fields = ['process', 'status', 'flow_task', 'started', 'finished', 'previous', 'token']

    @property
    def change_form_template(self):
        opts = self.model._meta

        return [
            "admin/%s/%s/change_form.html" % (opts.app_label, opts.model_name),
            "admin/%s/change_form.html" % opts.app_label,
            'admin/viewflow/task/change_form.html'
        ]

    def save_model(self, request, obj, form, change):
        result = super(TaskAdmin, self).save_model(request, obj, form, change)

        status_action = next((action[len('_change_status_'):]
                              for action in request.POST.keys()
                              if action.startswith('_change_status_')), None)
        if status_action:
            activation = obj.activate()
            activation_cls = activation.__class__
            transition = next((transition for transition in activation_cls.status.get_available_transtions(activation)
                               if transition.name == status_action), None)
            if transition:
                transition(activation)
                request.POST['_continue'] = True

        return result


admin.site.register(Process, ProcessAdmin)
admin.site.register(Task, TaskAdmin)
