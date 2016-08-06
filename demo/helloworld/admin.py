from django.contrib import admin
from viewflow.admin import ProcessAdmin, TaskAdmin
from . import models, flows


class HelloWorldProcessAdmin(ProcessAdmin):
    list_display = ['pk', 'created', 'status', 'participants',
                    'text', 'approved']
    list_display_links = ['pk', 'created']


class HelloWorldTaskAdmin(TaskAdmin):
    list_display = ['pk', 'created', 'status',
                    'owner', 'owner_permission', 'token',
                    'started', 'finished']
    list_display_links = ['pk', 'created']

    def get_queryset(self, request):
        qs = super(HelloWorldTaskAdmin, self).get_queryset(request)
        return qs.filter(process__flow_class=flows.HelloWorldFlow)


admin.site.register(models.HelloWorldProcess, HelloWorldProcessAdmin)
admin.site.register(models.HelloWorldTask, HelloWorldTaskAdmin)
