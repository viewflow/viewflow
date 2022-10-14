from django.contrib import admin, auth
from .models import Process, Task


class TaskInline(admin.TabularInline):
    """Task inline."""

    model = Task
    fields = ["flow_task", "flow_task_type", "status", "token", "owner"]
    readonly_fields = ["flow_task", "flow_task_type", "status", "token"]

    def has_add_permission(self, request, obj=None):
        """Disable manually task creation."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable task deletion in the process inline."""
        return False


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    """List all of viewflow process."""

    icon = '<i class="material-icons">assignment</i>'

    actions = None
    date_hierarchy = "created"
    list_display = ["pk", "created", "flow_class", "status", "participants", "brief"]
    list_display_links = ["pk", "created", "flow_class"]
    list_filter = ["status", "flow_class"]
    readonly_fields = ["flow_class", "status", "finished", "parent_task"]
    inlines = [TaskInline]

    def has_add_permission(self, request, obj=None):
        """Disable manually process creation."""
        return False

    def participants(self, obj):
        """List of users performed tasks on the process."""
        user_ids = obj.task_set.exclude(owner__isnull=True).values("owner")
        USER_MODEL = auth.get_user_model()
        username_field = USER_MODEL.USERNAME_FIELD
        users = USER_MODEL._default_manager.filter(pk__in=user_ids).values_list(
            username_field
        )
        return ", ".join(user[0] for user in users)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """List all of viewflow tasks."""

    icon = '<i class="material-icons">assignment_turned_in</i>'

    actions = None
    date_hierarchy = "created"
    list_display = [
        "pk",
        "created",
        "process",
        "status",
        "owner",
        "owner_permission",
        "token",
        "started",
        "finished",
    ]
    list_display_links = ["pk", "created", "process"]
    list_filter = ["status", "process__flow_class"]
    readonly_fields = [
        "process",
        "status",
        "flow_task",
        "started",
        "finished",
        "previous",
        "token",
    ]

    def has_add_permission(self, request, obj=None):
        """Disable manually task creation."""
        return False
