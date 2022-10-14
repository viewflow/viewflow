# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is licensed under the Commercial licence defined in file
# 'COMM_LICENSE', which is part of this source code package.

from django.db.models.query import QuerySet
from rest_framework.views import APIView
from rest_framework.response import Response


class FlowGraphView(APIView):
    flow_state_field = None
    lookup_field = 'pk'
    lookup_url_kwarg = None
    queryset = None

    def get_queryset(self):
        if self.queryset:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                # Ensure queryset is re-evaluated on each request.
                queryset = queryset.all()
            return queryset

    def get_object(self):
        queryset = self.get_queryset()
        if queryset is None:
            return

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        if lookup_url_kwarg not in self.kwargs:
            return

        obj = queryset.filter(
            **{self.lookup_field: self.kwargs[lookup_url_kwarg]}
        ).first()
        if not obj:
            return

        self.check_object_permissions(self.request, obj)
        return obj

    def get_flow_graph(self, obj=None):
        raise NotImplementedError

    def get(self, request, format=None):
        obj = self.get_object()
        flow = self.get_flow(obj)
        completed_states = self.get_completed_states(flow, obj)
        graph = self.get_get_flow_graph(completed_states)
        return Response(graph.to_json())
