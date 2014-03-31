django-viewflow
==============

Ad-hoc business process automation framework for Django


Development status
------------------

Prototype planning


Sample
------

    @transaction.atomic()
    def task(request, flow_task, task_id):
        task = get_object_or_404(Task, pk=task_id)

        if not flow_task.has_perm(request.user, task):
            raise PermissionDenied

        activation = flow_task.start(task, request.POST or None)
        form = MyForm(instance=task.process, request.POST or None)

        if form.is_valid():
            form.save()
            flow_task.done(activation)
            return redirect('viewflow:index', current_app=MyFlow.app_label)

       return render(request, templates, {'form': form, 'activation': activation},
                     current_app=MyFlow.namespace)


