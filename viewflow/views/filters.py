from django_filters.filterset import filterset_factory


class FilterableViewMixin(object):
    """
    A mixin that provides a way to show and handle a FilterSet in a request.
    """

    filterset_class = None
    filter_fields = None
    strict_filter = False

    def get_filterset_class(self):
        """
        Returns the filterset class to use in this view
        """
        if self.filterset_class:
            return self.filterset_class
        elif self.filter_fields:
            return filterset_factory(model=self.model, fields=self.filter_fields)

    def get_filterset_kwargs(self, filterset_class):
        """
        Returns the keyword arguments for instantiating the filterset.
        """
        kwargs = {}

        if self.viewset is not None and hasattr(self.viewset, "get_filterset_kwargs"):
            kwargs = self.viewset.get_filterset_kwargs(self.request)

        return {
            **kwargs,
            "data": self.request.GET or None,
            "request": self.request,
        }

    def get_filterset(self, filterset_class, queryset):
        """
        Returns an instance of the filterset to be used in this view.
        """
        kwargs = self.get_filterset_kwargs(filterset_class)
        return filterset_class(queryset=queryset, **kwargs)

    def is_strict_filter(self):
        return self.strict_filter

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset, filterset_class = None, self.get_filterset_class()
        if filterset_class is not None:
            self.filterset = self.get_filterset(filterset_class, queryset=queryset)
            if self.filterset.is_valid() or not self.is_strict_filter():
                queryset = self.filterset.qs
            else:
                queryset = self.filterset.queryset.none()
        return queryset
