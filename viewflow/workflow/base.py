import copy
from collections import defaultdict
from textwrap import dedent
from typing import Any, Dict, Iterator, List, Optional, Tuple

from django.apps import apps
from django.db import transaction
from django.urls import include, path
from django.urls.exceptions import NoReverseMatch
from django.utils.timezone import now

from viewflow.utils import (
    LazySingletonDescriptor,
    camel_case_to_title,
    has_object_perm,
    strip_suffixes,
)
from viewflow.urls import Viewset, ViewsetMeta
from viewflow.this_object import this
from .activation import Activation, _can_cancel
from .exceptions import FlowRuntimeError
from .status import STATUS, PROCESS
from . import lock


class Edge:
    """Represents an edge in the Flow graph.

    An edge connects two nodes (source and destination) in the flow graph and
    can have different types (e.g., `next`, `cond_true`, `cond_false`, `default`).

    Attributes:
        _src: The source node of the edge.
        _dst: The destination node of the edge.
        _edge_class: The class/type of the edge.
    """

    __slots__ = ("_src", "_dst", "_edge_class", "_label")

    def __init__(
        self, src: str, dst: str, edge_class: str, label: Optional[str] = None
    ) -> None:
        """
        Initializes an Edge instance.
        """
        self._src = src
        self._dst = dst
        self._edge_class = edge_class
        self._label = label

    @property
    def label(self) -> Optional[str]:
        """Optional edge caption (e.g. 'yes'/'no' on an If gateway)."""
        return self._label

    @property
    def src(self) -> str:
        """Edge source node."""
        return self._src

    @property
    def dst(self) -> str:
        """Edge destination node."""
        return self._dst

    @property
    def edge_class(self) -> str:
        """Type of the edge.

        Viewflow uses `next`, 'cond_true', `cond_false` and `default`
        edge classes.

        Edge class could be used as a hint for edge visualization.
        """
        return self._edge_class

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.src == other.src and self.dst == other.dst

    def __str__(self) -> str:
        return "[{}] {} ---> {}".format(self._edge_class, self._src, self._dst)


class Node(Viewset):
    """
    Base class for a flow task definition.

    :keyword task_type: Human readable task type
    :keyword activation_class: Activation implementation specific for this node
    """

    activation_class: Optional[type] = None
    flow_class: Optional[type] = None
    task_type: Optional[str] = None

    task_title: str = ""
    task_description: str = ""
    task_summary_template: str = ""
    task_result_template: str = ""

    def __init__(
        self,
        activation_class: Optional[type] = None,
        **kwargs: Any,
    ):  # noqa D102
        self._incoming_edges = []
        self._boundary_events = []
        self._boundary_specs = []
        self._compensation_handler = None
        self._is_compensation_handler = False
        self._multi_instance = False

        if activation_class:
            self.activation_class = activation_class

        super(Node, self).__init__(**kwargs)

    @property
    def name(self) -> str:
        """
        Get the name of the node."
        """
        return self.app_name

    @name.setter
    def name(self, value: str) -> None:
        self.app_name = value
        if not self.task_title:
            self.task_title = value.replace("_", " ").title()

    def _get_resolver_extra(self) -> Dict[str, Any]:
        """
        Get additional variable for view context
        """
        return {"node": self}

    def _outgoing(self) -> Iterator[Edge]:
        """
        Get an iterator over the outgoing edges of this node.

        :returns: An iterator over the outgoing edges of this node.
        :rtype: iterator
        """
        raise NotImplementedError

    def _incoming(self) -> Iterator[Edge]:
        """
        Get an iterator over the incoming edges of this node.

        :returns: An iterator over the incoming edges of this node.
        :rtype: iterator
        """
        return iter(self._incoming_edges)

    def bpmn_content(self):
        if self._multi_instance and (self.bpmn_element or "").endswith(
            ("Task", "Activity")
        ):
            return "<bpmn:multiInstanceLoopCharacteristics/>"
        return ""

    def bpmn_attrs(self):
        """Extra XML attributes for the node's BPMN element."""
        if self._is_compensation_handler:
            return {"isForCompensation": "true"}
        return {}

    def CompensateWith(self, node: Any) -> "Node":
        """
        Register a compensation handler for this task.

        The handler is a ``flow.Function`` node without incoming connections,
        executed by ``flow.CompensateThrow`` when the flow compensates.
        """
        self._compensation_handler = node
        return self

    def OnTimeout(
        self,
        delay: Any,
        then: Any,
        interrupting: bool = True,
        title: Optional[str] = None,
    ) -> "Node":
        """
        Attach a timer boundary event to this task.

        Fires the ``then`` path when ``delay`` elapses before the task
        completes. Interrupting by default (cancels the task);
        ``interrupting=False`` starts a parallel path and leaves it running.
        The boundary node is auto-named ``<task>__timeout``; pass ``title``
        to set its chart label. Chain before ``.Next()``.
        """
        from .flow.nodes import TimerBoundary

        boundary = TimerBoundary(None, delay=delay, interrupting=interrupting).Next(
            then
        )
        if title is not None:
            boundary.Annotation(title=title)
        self._boundary_specs.append(("timeout", boundary))
        return self

    def OnError(
        self,
        then: Any,
        code: Any = None,
        interrupting: bool = True,
        title: Optional[str] = None,
    ) -> "Node":
        """
        Attach an error boundary event to this task.

        Fires the ``then`` path when the task fails in a background context
        (job, function, timer). Pass ``code`` to catch only a matching
        ``flow.ErrorEnd`` code. The boundary node is auto-named
        ``<task>__error``; pass ``title`` to set its chart label. Chain
        before ``.Next()``.
        """
        from .flow.nodes import ErrorBoundary

        boundary = ErrorBoundary(None, code=code, interrupting=interrupting).Next(then)
        if title is not None:
            boundary.Annotation(title=title)
        self._boundary_specs.append(("error", boundary))
        return self

    def OnEscalation(
        self, then: Any, code: Any = None, title: Optional[str] = None
    ) -> "Node":
        """
        Attach a non-interrupting escalation boundary event to this task.

        Fires the ``then`` path when a ``flow.EscalationThrow`` is raised
        inside this subprocess, without interrupting it. The boundary node is
        auto-named ``<task>__escalation``; pass ``title`` to set its chart
        label. Chain before ``.Next()``.
        """
        from .flow.nodes import EscalationBoundary

        boundary = EscalationBoundary(None, code=code).Next(then)
        if title is not None:
            boundary.Annotation(title=title)
        self._boundary_specs.append(("escalation", boundary))
        return self

    def __str__(self) -> str:
        if self.name:
            return self.name.title().replace("_", " ")
        return super(Node, self).__str__()

    def _resolve(self, instance: "Flow") -> None:
        """Node class should resolve other nodes this-references here.

        Called as soon as node instances infatuated, but before
        incoming/outgoing links set.
        """

    def _ready(self) -> None:
        """
        Called when the flow class setup is finished.

        Subclasses can perform additional initialization here.
        """

    def _create(
        self,
        prev_activation: "Activation",
        token: str,
        data: Optional[Dict[str, Any]] = None,
        seed: Optional[Any] = None,
    ) -> "Activation":
        """
        Create a new task instance.

        :param prev_activation: The previous activation in the flow.
        :type prev_activation: Activation
        :param token: The token to use for the new task instance.
        :type token: str
        :returns: The new activation instance.
        :rtype: Activation
        """
        activation = self.activation_class.create(
            self, prev_activation, token, data=data, seed=seed
        )
        for boundary_event in self._boundary_events:
            boundary_event._arm(activation)
        return activation

    def Annotation(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        summary_template: Optional[str] = None,
        result_template: Optional[str] = None,
    ) -> "Node":
        """
        Sets annotation for the node.

        :param title: The title for the task
        :param description: The description for the task
        :param summary_template: The template for the task summary
        :param result_template: The template for the task result
        :return: The node instance with the updated annotation values
        """
        if title is not None:
            self.task_title = title
        if description is not None:
            self.task_description = description
        if summary_template is not None:
            self.task_summary_template = summary_template
        if result_template is not None:
            self.task_result_template = result_template
        return self

    def _get_transition_url(self, activation: Activation, transition: Any) -> str:
        url_name = transition.slug
        if url_name == "start":
            url_name = "execute"

        return activation.flow_task.reverse(
            url_name, args=[activation.process.pk, activation.task.pk]
        )

    def get_available_actions(
        self, activation: Activation, user: Any
    ) -> Iterator[Tuple[str, str]]:
        """
        Returns a list of available actions for the given user on the current node.

        :param activation: The current activation instance.
        :type activation: viewflow.models.Activation
        :param user: The user to check actions for.
        :type user: django.contrib.auth.models.User
        :return: A list of available actions as a tuple of (name, url).
        :rtype: list
        """
        # fmt: off
        transitions = activation.get_available_transitions(user)
        for transition in transitions:
            try:
                url = self._get_transition_url(activation, transition)
            except NoReverseMatch:
                pass
            else:
                yield transition.label, url


class FlowMetaClass(ViewsetMeta):
    def __str__(self) -> str:
        from .fields import get_flow_ref

        return get_flow_ref(self)


class Flow(Viewset, metaclass=FlowMetaClass):
    """
    Base class for defining a task in a flow.

    :param task_type: A human-readable string describing the task type.
    :type task_type: str
    :param activation_class: The activation class to use for this node. If not
        specified, a default activation class will be used.
    :type activation_class: class
    """

    instance: Optional["Flow"] = None

    process_class: Optional[type] = None
    task_class: Optional[type] = None
    lock_impl: Any = lock.no_lock

    process_title: str = ""
    process_description: str = ""
    process_summary_template: str = ""
    process_result_template: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Create a new node instance.

        :param activation_class: The activation class to use for this node.
        :type activation_class: class
        :param kwargs: Additional keyword arguments to pass to the superclass.
        """
        super().__init_subclass__(**kwargs)
        cls.instance = LazySingletonDescriptor()

        # process and task default values
        from .models import Process, Task  # avoid app not loaded error

        if cls.process_class is None:
            cls.process_class = Process
        if cls.task_class is None:
            cls.task_class = Task

        # viewset.app_name
        cls.app_name = strip_suffixes(cls.__name__, ["Flow"]).lower()

        # flow description
        if not cls.process_title or not cls.process_description:
            if cls.__doc__:
                docstring = cls.__doc__.split("\n\n", 1)
                if not cls.process_title and len(docstring) > 0:
                    cls.process_title = docstring[0].strip()
                if not cls.process_description and len(docstring) > 1:
                    cls.process_description = dedent(docstring[1]).strip()
            else:
                if not cls.process_title:
                    cls.process_title = camel_case_to_title(
                        strip_suffixes(cls.__name__, ["Flow"])
                    )

        # nodes collect/copy
        cls._nodes_by_name = {}
        for attr_name in dir(cls):
            if attr_name.startswith("_") or attr_name == "instance":
                continue
            node = getattr(cls, attr_name)
            if not isinstance(node, Node):
                continue

            node = copy.copy(node)
            node.name = attr_name
            node.flow_class = cls
            cls._nodes_by_name[attr_name] = node
            setattr(cls, attr_name, node)

        # materialize fluent boundary events (.OnTimeout/.OnError/...) into
        # auto-named nodes attached to their host, so they wire like any
        # explicitly declared .OnTimeout boundary node
        materialized = {}
        for host_name, node in list(cls._nodes_by_name.items()):
            for suffix, boundary in getattr(node, "_boundary_specs", []):
                boundary = copy.copy(boundary)
                boundary_name = "{}__{}".format(host_name, suffix)
                index = 2
                while (
                    boundary_name in cls._nodes_by_name or boundary_name in materialized
                ):
                    boundary_name = "{}__{}_{}".format(host_name, suffix, index)
                    index += 1
                boundary.name = boundary_name
                boundary.flow_class = cls
                boundary._attached_to = node
                materialized[boundary_name] = boundary
                setattr(cls, boundary_name, boundary)
        for boundary_name, boundary in materialized.items():
            cls._nodes_by_name[boundary_name] = boundary

        # resolve inner links
        for _, node in cls._nodes_by_name.items():
            node._resolve(cls.instance)

        # setup flow graph
        incoming = defaultdict(lambda: [])  # node -> [incoming_nodes]
        for _, node in cls._nodes_by_name.items():
            for outgoing_edge in node._outgoing():
                incoming[outgoing_edge.dst].append(outgoing_edge)
        for target, edges in incoming.items():
            target._incoming_edges = edges

        # wire compensation handlers: mark the handler node and give it a
        # synthetic edge so the chart places it next to its host
        for _, node in cls._nodes_by_name.items():
            if node._compensation_handler is not None:
                handler = this.resolve(cls.instance, node._compensation_handler)
                node._compensation_handler = handler
                handler._is_compensation_handler = True
                handler._incoming_edges.append(
                    Edge(src=node, dst=handler, edge_class="compensation")
                )

        # mark multi-instance targets of data-source split branches
        for _, node in cls._nodes_by_name.items():
            for branch in getattr(node, "_branches", None) or []:
                if len(branch) == 4 and (branch[2] or branch[3]):
                    branch[0]._multi_instance = True

        # process permissions
        process_options = cls.process_class._meta
        for permission in ("manage",):
            if permission not in process_options.default_permissions:
                process_options.default_permissions += (permission,)

        # complete node setup
        for _, node in cls._nodes_by_name.items():
            node._ready()

    def __str__(self) -> str:
        return str(self.process_title)

    def _get_resolver_extra(self) -> Dict[str, Any]:
        """
        Get additional context for views
        """
        return {"flow": self}

    @classmethod
    def lock(cls, process_pk: int) -> Any:
        """
        Acquire a lock for the specified process.
        """
        return lock.lock_scope(cls.lock_impl, cls, process_pk)

    @property
    def app_label(self) -> str:
        """
        Get the application label for the flow.
        """
        module = "{}.{}".format(self.__module__, self.__class__.__name__)
        app_config = apps.get_containing_app_config(module)
        return app_config.label

    @property
    def flow_label(self) -> str:
        """
        Get the flow label for the flow.
        """
        module = "{}.{}".format(self.__module__, self.__class__.__name__)
        app_config = apps.get_containing_app_config(module)

        subpath = module[len(app_config.module.__name__) + 1 :]
        if subpath.startswith("flows."):
            subpath = subpath[len("flows.") :]
        if subpath.endswith("Flow"):
            subpath = subpath[: -len("Flow")]

        return subpath.lower().replace(".", "/")

    def nodes(self) -> Iterator[Node]:
        return self._nodes_by_name.values()

    def node(self, name: str, no_obsolete: bool = False) -> Optional[Node]:
        """
        Get a node by name.
        """
        node = self._nodes_by_name.get(name, None)
        if node is None and not no_obsolete:
            from .nodes import Obsolete

            obsolete_factory = self._nodes_by_name.get("obsolete", Obsolete())
            node = obsolete_factory.create_node(name, flow_class=self.__class__)
        return node

    def has_view_permission(self, user: Any, obj: Optional[Any] = None) -> bool:
        return user.is_authenticated and has_object_perm(
            user, "view", self.process_class, obj=obj
        )

    def has_manage_permission(self, user: Any, obj: Optional[Any] = None) -> bool:
        return user.is_authenticated and has_object_perm(
            user, "manage", self.process_class, obj=obj
        )

    def _get_urls(self) -> List:
        urlpatterns = super()._get_urls()

        for node in self.nodes():
            node.parent = self
            patterns, app_name, namespace = node.urls
            urlpatterns.append(
                path("", include((patterns, app_name), namespace=namespace))
            )

        return urlpatterns

    def _this_owner(self, flow_task: type) -> Any:
        """Return user that was assigned to the task."""

        def get_task_owner(activation):
            flow_class = activation.process.flow_class
            task_class = flow_class.task_class

            task = (
                task_class._default_manager.filter(
                    process=activation.process, flow_task=flow_task, status=STATUS.DONE
                )
                .order_by("-id")
                .first()
            )
            return task.owner if task else None

        return get_task_owner

    @classmethod
    def get_start_nodes(cls, user: Optional[Any] = None) -> List[Node]:
        """
        List of flow start nodes.

        If user is not None, returns only permitted nodes for the provided user
        """
        from .nodes import Start

        return [
            node
            for node in cls.instance.nodes()
            if isinstance(node, Start)
            if user is None or node.can_execute(user)
        ]

    def get_available_process_actions(
        self,
        process: Any,
        user: Optional[Any] = None,
    ) -> List[Dict[str, str]]:
        """List of {name, url} process actions available for the current user"""
        # TODO process cancel
        return []

    def cancel(self, process: Any) -> None:
        # Lock first, transaction second, so the lock outlives the commit --
        # otherwise a CacheLock is released before cancel's writes are
        # visible and a concurrent activation reads the pre-cancel snapshot.
        with self.lock(process.pk), transaction.atomic():
            active_tasks = process.task_set.exclude(
                status__in=[STATUS.DONE, STATUS.CANCELED, STATUS.REVIVED]
            )

            activations = [
                task.flow_task.activation_class(task) for task in active_tasks
            ]

            not_cancellable = [
                activation for activation in activations if not _can_cancel(activation)
            ]
            if not_cancellable:
                raise FlowRuntimeError(
                    "Can't cancel {}".format(
                        ",".join(str(activation.task) for activation in not_cancellable)
                    )
                )

            for activation in activations:
                activation.cancel()

            process.status = PROCESS.CANCELED
            process.finished = now()
            process.save()
