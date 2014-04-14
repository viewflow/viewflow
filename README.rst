django-viewflow
==============

Ad-hoc business process automation framework for Django


Development status
------------------

Prototype planning


Sample
------
```python
    @flow_view()
    def task(request, activation):
        activation.prepare(request.POST or None)
        form = MyForm(instance=task.process, request.POST or None)

        if form.is_valid():
            form.save()
            activation.done()
            return redirect('viewflow:index', current_app=MyFlow.app_label)

       return render(request, templates, {'form': form, 'activation': activation},
                     current_app=MyFlow.namespace)


```
