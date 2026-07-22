=========
Changelog
=========

2.4.0
-----

- Fix 500 on the admin process changelist: the ``flow_class`` list filter
  executed the changelist participants prefetch against materialized flow
  classes (#523). The filter now builds its choices from the plain model
  manager and labels them with the flow's ``process_title``.
- Fix 500 on the workflow task detail page when a ``Subprocess`` child flow
  is not registered as a viewset — the subprocess link degrades to plain
  text instead of raising ``NoReverseMatch``.
- BPMN 2.0 export overhaul: exported files now pass validation against the
  official OMG schema and open in bpmn.io/Camunda Modeler. ``Switch``,
  ``Subprocess`` and ``NSubprocess`` nodes are no longer dropped from the
  export (previously leaving dangling ``sequenceFlow`` references); they map
  to an exclusive gateway and call activities (with a multi-instance marker
  for ``NSubprocess``).
- More faithful BPMN element mapping: ``Handle`` exports as ``receiveTask``,
  celery ``Job`` as ``serviceTask``, ``StartHandle`` as a message start
  event, a conditional ``Split`` as an inclusive gateway, and a ``Join``
  with ``continue_on_condition`` as a complex gateway. ``If`` branches are
  labeled yes/no and ``Switch`` marks its default flow.
- Download a flow's BPMN file from the chart view and the REST API with
  ``?format=bpmn``, in addition to the ``flowexport`` management command.
- New database-backed ``flow.Timer`` node: the due moment is stored on the
  task row (new ``Task.scheduled`` field, migration included) and survives
  a message broker restart or flush, unlike ``celery.Timer``. Due timers
  are fired by the ``workflow_timers`` management command (cron) or the
  ``viewflow.workflow.tasks.workflow_fire_timers`` celery beat task.
- New ``flow.StartTimer(interval=...)`` node starts a process on schedule,
  fired by the same dispatcher; exports as a BPMN timer start event.
- New boundary events, declared fluently on the host task (chained before
  ``.Next()``): ``.OnTimeout(delay, then)`` fires a deadline/escalation path
  when the delay elapses before the task completes; ``.OnError(then,
  code=...)`` catches a background task failure and routes it to a recovery
  path. Interrupting by default (cancels the host task);
  ``interrupting=False`` starts a parallel path instead. Exported as BPMN
  boundary events drawn on the host task's border.
- New ``flow.TerminateEnd()`` cancels all other active tasks and finishes
  the process immediately (BPMN terminate end event).
- New ``flow.ErrorEnd(code)`` interrupts the process and records it as
  failed; inside a subprocess the parent task is marked ``ERROR`` so the
  parent's ``.OnError(this.recover, code=...)`` boundary catches it.
- Compensation support: ``.CompensateWith(this.handler)`` registers an
  undo handler on any task; ``flow.CompensateThrow()`` runs the handlers
  of completed tasks in reverse completion order, each at most once.
  Exported as compensation boundary events with associations.
- New task-type nodes with dedicated BPMN export and chart markers:
  ``flow.SendHandle`` (send task), ``flow.BusinessRule`` (business rule
  task), and ``flow.ManualTask`` -- work performed outside any system,
  marked done from the task list with a no-field confirmation form.
- ``flow.NSubprocess(..., sequential=True)`` runs one child process at a
  time. ``flow.Split`` branches with ``task_data_source`` now mark their
  target activity multi-instance in the BPMN export and SVG chart.
- New intermediate events: ``flow.MessageCatch``/``flow.MessageThrow``
  (message catch/throw), ``flow.SignalCatch``/``flow.SignalThrow``
  (broadcast -- one throw releases every armed catch across processes and
  flow classes), ``flow.EscalationThrow`` with a non-interrupting
  ``.OnEscalation`` boundary (notify a parent subprocess without
  interrupting it), and ``flow.ConditionalCatch`` (waits until a condition
  over process data holds, fired by the ``workflow_timers`` dispatcher).
  All exported with the matching BPMN event definitions.
- Chart layout: empty grid rows/columns are now collapsed and cell
  collisions resolved (fixing overlapping nodes); edge routing staggers
  parallel channels, routes around node shapes, and renders ``If`` yes/no
  labels in the SVG.
- ``InlineFormSetField`` (and the other composite form fields) now honor a
  field-level ``initial=[...]`` argument as a fallback when the bound form
  provides no initial for that field, so pre-populated formset rows render
  their values.
- FSM (``viewflow.fsm``): the ``FlowViewsMixin`` list page now shows the state
  diagram alongside the object table, in a click-to-zoom dialog matching the
  BPMN process chart. The diagram (and the one in the Django admin change list)
  can be exported as a PNG image. The admin change-list graph is now sized so
  it no longer blows out the filter sidebar and hides the object list.
- Workflow ``flow.View`` gained an optional ``reassign_view_class`` hook,
  finishing the built-in (owner/manager-gated) ``reassign`` transition: point
  it at a view that collects the target user and calls
  ``activation.reassign(user=...)``, and a "Reassign" action button appears on
  the task. Off by default (delegation policy is application-specific). See the
  new ``substitute`` cookbook sample.
- New ``snooze`` cookbook sample: hide a human task from the inbox until a
  chosen time, with a dedicated "Snoozed" menu entry next to Inbox/Queue/
  Archive (issue #219). Implemented entirely in application code -- a
  ``flow.View`` subclass adds ``snooze``/``unsnooze`` task actions storing the
  wake-up time in ``task.data``, and a ``FlowAppViewset`` subclass filters the
  inbox and adds the Snoozed list. No background worker and no core change: a
  task is snoozed only while its stored wake-up time is in the future.
- New ``dynamic_subprocess`` cookbook sample: start additional ``NSubprocess``
  children while the parent task is still running (issue #258). A custom
  "Add item" action on the order's process-detail page attaches one more child
  process to the still-``STARTED`` ``NSubprocess`` task -- calling the same
  ``start_subprocess_task.run(_parent_task=task, item=...)`` the node uses to
  fan out -- so the join now also waits for the added item. No core change.
- Every built-in control node is now cancellable: ``Split``, ``Switch``,
  ``End`` (and ``TerminateEnd``/``ErrorEnd``) and ``CompensateThrow`` gained
  a ``cancel`` transition (from ``ERROR``), so cancelling a process that has
  one of them stuck in ``ERROR`` no longer raises ``AttributeError``.
- ``Flow.cancel`` (and the join/end cancel helpers) now raise the intended
  ``FlowRuntimeError`` -- not ``AttributeError`` -- when an active task's node
  defines no ``cancel`` transition (e.g. a custom node).
- The process cancel view no longer 500s when an active task can't be
  cancelled (e.g. a ``View`` a user still has open, in ``STARTED``): it
  refuses cleanly with a flash message and disables the cancel button while
  such tasks are active.
- The flow diagram modal is now pan- and zoom-able: scroll to zoom toward
  the cursor, drag to pan, pinch to zoom on touch devices, and double-click
  to reset -- making large, complex flow charts readable. The zoomed diagram
  is clipped to the dialog (no longer spilling over the page) and the close
  button stays on top. Implemented natively in the ``vf-modal-trigger``
  component with no added dependency.
- The flow diagram dialog gained a BPMN export button that downloads the
  chart as a ``.bpmn`` file (the same ``?format=bpmn`` the chart view already
  served), on both the flow dashboard and the process detail panel.
- ``process_dashboard.html`` now exposes a ``flow_start_card_actions`` block,
  so projects can append controls to the start card by extending the template
  instead of copying it (the bundled demo override now does this and no longer
  drifts from the library template).
- Fix a bulk-action crash on "Select All" for a model viewset without a
  configured filter (no ``list_filterset_class`` / ``list_filter_fields``):
  ``objects_count`` dereferenced a ``None`` filterset and raised
  ``AttributeError: 'NoneType' object has no attribute 'form'`` (#422).
- Bulk actions now scope their base queryset through the viewset's
  ``get_queryset(request)``, the same way the list view does, so a
  "Select All" delete no longer operates on rows outside the viewset's
  scope (e.g. other accounts' records).
- A virtual list column (a viewset/model method or property) can now be
  made sortable by declaring an ``orderby_column`` -- a field-lookup string
  (e.g. ``"data__price"`` to sort by a ``JSONField`` key) or a query
  expression (e.g. ``Cast("data__price", IntegerField())`` for a numeric
  sort). Expression-ordered columns now also render the sort-direction
  indicator in the header (#361).
- New ``jsonstore.ForeignKey`` field: reference another model from data kept
  in a JSONField. The related object's pk is stored under ``<name>_id``,
  ``instance.<name>`` loads it lazily, and ``formfield()`` is a
  ``ModelChoiceField`` so it works in forms, viewsets and the admin. Like the
  other JSON Store fields it needs no column or migration; being document-based
  it has no DB constraint, reverse accessor, or join support (query via
  ``filter(data__<name>_id=...)``). Target models with a non-integer (e.g.
  ``UUIDField``) primary key are supported (#366).
- New JSON Store field types: ``BigIntegerField``, ``SmallIntegerField``,
  ``PositiveIntegerField``, ``PositiveSmallIntegerField``,
  ``PositiveBigIntegerField``, ``SlugField``, ``FilePathField``,
  ``UUIDField`` (stored as a string, read back as a ``uuid.UUID``),
  ``DurationField`` (stored as an ISO-8601 duration, read back as a
  ``timedelta``) and ``BinaryField`` (stored base64-encoded, read back as
  ``bytes``).
- New ``jsonstore.OneToOneField``: a one-to-one relation stored in the
  JSONField, identical to ``jsonstore.ForeignKey`` on the forward side; being
  document-based it enforces no ``UNIQUE`` constraint.
- New ``jsonstore.ManyToManyField``: a many-to-many relation kept as a list of
  primary keys inside the JSONField, with no join table. ``instance.<name>``
  is a manager with ``all``/``add``/``remove``/``set``/``clear``/``count``, and
  ``formfield()`` is a ``ModelMultipleChoiceField`` that persists a form
  selection. The manager mutates the in-memory document (call ``save()`` to
  persist); there is no ``through`` model or reverse accessor. UUID-pk targets
  are supported (#366).
- JSON Store fields gained a ``json_key`` argument to control where the value
  is stored inside the document: a string for a custom key, or a list/tuple for
  a nested path (``json_key=("address", "city")`` -> ``data["address"]["city"]``,
  with intermediate dicts created automatically and shareable between fields).
  The custom key / nested path is honored by reading, writing, filtering and
  ordering, and works with every field type including the relation fields.
- New ``jsonstore.EmbeddedModel`` / ``jsonstore.EmbeddedField``: a schema-only
  "virtual model" (typed fields, no table) embedded in a host model as a nested
  JSON document. Typed fields serialize at depth, ``json_key`` works inside the
  document, an embedded model can nest another, and reading returns an instance
  bound to the stored sub-document so in-place edits are saved. Query nested
  values through the raw JSON key (``filter(data__price__amount=...)``) (#366).
- New ``jsonstore.EmbeddedListField``: store a list of ``EmbeddedModel``
  instances as an array of JSON documents (the embedded-document analogue of
  ``ManyToManyField``). ``instance.<name>`` is a mutable, list-like accessor
  (indexing, iteration, ``append``, ``insert``, ``del``); each element is bound
  to its stored document so in-place edits are saved. Accepts ``json_key`` /
  ``json_field_name`` (#366).
- ``viewflow.forms`` can now edit embedded documents as nested forms:
  ``EmbeddedModelForm`` builds a form from an ``EmbeddedModel`` schema, and the
  ``EmbeddedFormField`` / ``EmbeddedFormSetField`` composite fields bind it to a
  ``jsonstore.EmbeddedField`` / ``EmbeddedListField`` -- so a document edits as a
  nested form and a list of them edits as inlines, all saved to the one JSON
  column. New ``cookbook/embed101`` demo (mounted at ``/embedded/``) with a raw-
  JSON admin (#366).

2.3.2  2026-07-06
-----------------

- Fix cross-flow privilege escalation: a user with only flow A's ``manage``
  permission could cancel flow B's process by posting flow B's process id to
  flow A's cancel URL. ``CancelProcessView`` now scopes its queryset to the
  view's own flow.
- Fix the bulk-delete endpoint (``action/delete/``): it deleted rows without
  checking login or the ``delete`` permission. Both checks now run before any
  delete. The gap mattered most for a ``ModelViewset`` mounted outside a
  ``Site``/``Application`` wrapper, where no other layer enforced auth.
- Fix cross-flow information disclosure: a user with only flow A's ``view``
  permission could read flow B's process detail, including its full task
  list, by opening flow B's process id on flow A's URL.
  ``DetailProcessView`` now scopes its queryset to the view's own flow.
- Fix a 500 error on any list view without ``search_fields`` set: appending
  ``?_search=`` crashed the view instead of being ignored.
- Fix a crash on the admin change page of any FSM-backed model under
  Django 5.2+ (incl. 6.1): the ``change_form_fsm_tools`` template tag called
  ``InclusionAdminNode`` with the old signature after Django added a required
  ``name`` first argument, raising ``TypeError`` while rendering.
- Fix a transaction-ordering bug that committed partial writes alongside a
  task's ``ERROR`` status. In async mode (e.g. after a JOB node), the
  exception guard swallowed the error before the surrounding savepoint saw
  it, so the savepoint rolled back nothing. Affects ``Function``, ``End``,
  ``If``, ``Split``, and ``Switch`` nodes.
- Wrap ``Subprocess`` and ``NSubprocess`` activation in a savepoint too, so a
  failure while computing subprocess data or spawning children rolls back the
  partial work instead of leaving it (and half-spawned children) committed
  next to the ``ERROR`` status, where a ``retry`` would double-spawn them.
- Guard ``Join`` completion the same way. An error while completing a join
  (a partial-join cancel failing, a malformed multi-token join, or a
  ``task_finished`` receiver raising) now follows the activation context: a
  background trigger (e.g. a ``Job`` node) records ``STATUS.ERROR`` on the join
  and rolls back the partial cancel, leaving the process recoverable instead of
  crashing the worker, while a user/synchronous trigger propagates the error to
  its caller. ``is_done`` is now a side-effect-free predicate; the branch
  cancellation it used to perform runs inside the guarded ``complete()``.
- Fix a celery ``Job`` node treating ``self.retry()`` as a task failure.
  ``Retry`` (and ``Reject``) is a control-flow signal, not an error; it now
  passes through instead of marking the task ``ERROR``. The redelivered retry
  also used to hit ``TransitionNotAllowed`` because ``start()`` only accepted a
  ``SCHEDULED`` task while a retry re-enters a ``STARTED`` one; ``start()`` now
  accepts ``STARTED`` too, so the retried run restarts, runs, and completes
  (the process lock still serialises concurrent deliveries).
- Fix ``ImportViewsetMixin``'s "Import" button linking to a view with no
  ``form_class``, which 500ed on every GET. It now renders a real upload
  form and imports the submitted file via ``django-import-export``.
- Fix a formset validation bypass: a form with an ``InlineFormSetField``
  reported valid, and saved the parent, even when the formset's
  ManagementForm was missing or tampered with. The real error lived in
  ``non_form_errors()``, which the check never looked at.
- Fix grouped ``<select>`` choices (options nested under an ``<optgroup>``)
  being silently dropped except for the first option in each group.
  Affects ``Select``, ``RadioSelect``, and ``DependentModelSelect``.
- Fix an unbounded memory leak in form rendering: the widget-renderer cache
  was keyed on the widget *instance*, and Django deep-copies widgets per
  form, so every render pinned a new widget/field/form from garbage
  collection forever with zero cache hits. Now cached by widget class.
- Fix ``viewflow.fsm``'s default ``get_object_flow()`` (``FlowViewsMixin``,
  ``FlowRESTMixin``, ``FlowAdminMixin``) always raising, even for a flow
  class with a valid single-argument constructor. It called
  ``get_flow_state()`` without the required ``request`` argument; the
  resulting ``TypeError`` was swallowed and rebranded as a misleading
  "no constructor with single argument" error.
- Fix ``viewflow.fsm``'s REST ``transitions`` action, which hardcoded the
  demo's URL name and namespace ("review-transition", "review:..."). Any
  ``FlowRESTMixin`` viewset with a different basename or namespace hit
  ``NoReverseMatch`` (500) on ``GET /{pk}/transition/``. Now built from
  the viewset's own basename and the request's resolved namespace.
- Fix ``jsonstore`` fields with a falsy ``default`` (``BooleanField(default=False)``,
  ``IntegerField(default=0)``) returning ``None`` instead of the default when
  the underlying JSON key is absent. The default was checked with a
  truthiness test instead of an identity check against "not provided".
- Fix ``vf-field-select-multiple`` silently dropping the last selected value when
  deselecting a non-last item with 3+ items selected. A duplicated ``splice()``
  call removed an extra entry from the selection array; the array logic is now
  in a small, independently unit-tested module.
- Fix ``vf-field-select-multiple`` sometimes failing to deselect an item on
  click/keypress at all. The underlying MDC list ran its own native checkbox
  toggle in addition to (not instead of) our custom selection handling, so a
  single interaction toggled the same selection array through two independent
  code paths.
- Fix ``InlineCalendar`` always submitting an empty value: the hidden input
  read a Solid signal *accessor* function instead of calling it, so the
  picked date was silently dropped on every submit.
- Fix the JSON editor field (``JSONEditorWiget``) corrupting its value on every
  edit: the editor's internal ``Content`` wrapper (``{json: ...}`` or
  ``{text: ...}``) was stored directly instead of the value inside it.
- Fix the autocomplete field (single and multi-select) crashing on Enter when
  no suggestion was selected, which stopped the form from being submitted
  properly.
- Fix ``ListModelView.get_object_url`` crashing with ``AttributeError`` when
  used standalone (no ``viewset``) on a model with ``get_absolute_url``. It
  called a misspelled method name.
- Fix an unbounded memory leak in ``ListModelView``: an ``lru_cache`` keyed on
  the view instance pinned every list view ever rendered. Now cached per
  instance instead.
- Fix ``Transition.can_proceed(check_conditions=False)`` returning ``False``
  even when the transition exists. It now skips the condition check instead
  of reporting the transition as unavailable.
- Fix ``fsm.State`` with a custom getter replacing a falsy-but-valid state
  (``0``, ``False``) with the field's default. Only a missing value (``None``
  or ``""``) falls back to the default now.
- Fix ``viewflow.fsm``'s state/transition descriptors treating a falsy flow
  instance (one whose ``__len__`` returns ``0``) as a class-level access.
  Reading state or calling a transition on such an instance now works
  instead of raising ``TypeError``.
- Fix the FSM REST ``transition`` action committing a field update even
  when the transition itself failed. The update and the transition now run
  in one transaction.
- Fix the FSM REST ``transition`` action letting a user permitted to
  perform one transition write any other writable field on the same
  request. Add ``get_transition_fields()`` (default: none writable),
  matching the admin and viewset layers.
- Add a state chart view to ``FlowViewsMixin``: a ``chart/`` URL and a
  "State chart" list-page action, showing the same diagram the admin
  already renders. Replaces the dead, unrunnable ``FlowGraphView``.
- Fix a transition with no explicit ``target`` (a state-machine
  "self-transition") drawing a bogus ``"DEFAULT"`` node in the FSM chart.
  ``target=None`` (a real but ambiguous case) is now rejected at
  decoration time instead of silently mishandled.
- Fix ``jsonstore`` fields discarding a falsy-but-valid assigned value
  (``obj.n = 0``) on a ``blank=True`` field, silently falling back to
  the field's default on the next read. Only a genuinely empty value
  (``None`` or ``""``) is dropped now.
- Fix ``jsonstore`` fields silently mis-sorting on ``order_by()``: it
  sorted rows by the underlying JSON blob's raw text instead of the
  extracted value (e.g. integer ``9`` sorted after ``10``).
- Fix the ``VIEWFLOW`` setting silently ignoring every key except
  ``WIDGET_RENDERERS`` (an explicit ``AUTOREGISTER`` was dropped). Also
  fix ``AUTOREGISTER``'s default failing to recognize viewflow when
  installed via its explicit AppConfig path
  (``"viewflow.apps.ViewflowConfig"``), which silently skipped
  registering ``SiteMiddleware``.
- Fix ``SiteMiddleware`` crashing with ``TypeError`` on a
  ``TemplateResponse`` built with no explicit context, as soon as the
  app injects any context data.
- Fix ``viewflow.contrib.plotly``'s Dash endpoints (layout, dependencies,
  update-component) having no authentication check, letting an
  unauthenticated client read a dashboard's data and invoke its
  callbacks with arbitrary input.
- Fix ``ExportView`` (``contrib.import_export``) having no permission
  check, letting a user denied the list view export the whole table
  anyway.
- Fix avatar upload accepting any file as an image, with no size limit.
- Fix ``RedisLock``: its TTL is now renewed while the lock is held, and
  releasing an already-expired lock no longer raises.
- Fix cancelling a subprocess task raising ``FlowLockFailed`` when the
  child flow uses ``CacheLock``.
- Fix a synchronously-failing first node leaving an orphaned, task-less
  process row behind when the flow is started with ``start.run()``.
- Fix ``FlowChartView`` having no permission check on a standalone
  ``FlowViewset``, letting an anonymous user view the flow and
  per-process charts.
- Fix task actions releasing their lock before the transaction commits,
  letting a concurrent request double-execute the action under
  ``CacheLock``.
- Fix an N+1 query on the flow inbox and queue list pages.
- Fix a nested form's full HTML rendering into an unused ``value``
  attribute on its wrapper element.
- Fix a form ``Row``/``Column`` layout with an uneven ``AUTO`` split
  silently leaving a gap instead of raising an error.
- Fix the autocomplete/dependent-select AJAX endpoints crashing with a
  500 on a malformed ``field`` name.
- Fix the autocomplete endpoint crashing with a 500 when the requested
  field doesn't use an Ajax-aware widget.
- Fix a dependent select's pre-filled value failing to cascade to
  chained child selects when editing an existing record.
- Fix the autocomplete and dependent-select fields showing stale
  results when a slower request resolves after a newer one.
- Fix the autocomplete field clearing an already-selected value when a
  modifier key like Shift or Ctrl was pressed afterward.
- Fix a form validation error permanently disabling Turbo navigation
  for the rest of the session.
- Fix form buttons staying disabled forever after a failed submit or
  a Back navigation.
- Fix the calendar dropping day 1 for Monday-first locales when the
  month starts on a Sunday.
- Fix the calendar skipping a month when navigating from a day that
  doesn't exist in the next month, like Jan 31.
- Remove the time field's clock icon, which opened a dialog that
  never worked. Type the time directly instead.
- Fix the list filter drawer leaking its listeners on every page
  navigation.
- Fix the profile avatar upload silently failing instead of showing
  an error when no image was selected.
- Fix ``flowexport --format`` silently writing an empty file for an
  unknown format instead of raising an error.
- Fix permission setup creating content types in the wrong database
  in multi-database setups.
- Fix a crash in an internal, currently-unused helper
  (``parent_tasks_completed``).
- Fix a join or split raising the wrong error when it can't cancel a
  branch that already started.
- Fix a rare crash when every branch feeding a join was cancelled
  right before the join completed.
- Fix a crash in an unreachable fallback path of the task revive
  view.
- Fix the process cancel confirmation messages showing a literal
  ``{self.object.pk}`` instead of the process number.
- Fix a user with object-level (not model-wide) view permission on a
  process being wrongly denied access to its task detail pages.
- Speed up the flow dashboard's process and task lists, which ran a
  database query per row.
- Add a system check warning when a flow has Join nodes but no real
  lock, which can create duplicate join tasks under concurrency.
- Speed up the process admin's participants column, which ran two
  database queries per row.
- Fix a stray ``$`` corrupting the first custom CSS class on
  rendered icons.
- Fix a plain-object flow's state reverting to its default after
  being pickled and unpickled in a different process.
- Fix deleting a ``CompositeKey`` row skipping cascades and always
  overriding a model's own ``delete()`` method.
- Fix list views linking a column whose name happens to be a
  substring of the intended link column.
- Fix the "Administration" menu entry showing to every logged-in
  user instead of just staff.
- Fix the formset field leaking its "add" button listener on every
  Turbo navigation.
- Fix list tables leaking their column-sort click listener on every
  Turbo navigation.
- Fix the modal trigger leaking its button click listener on every
  disconnect.
- Fix the date field stacking a new listener every time its calendar
  dialog was reopened.
- Fix the autocomplete field's Escape key throwing an error instead
  of clearing the highlighted suggestion.
- Fix the total field leaking its internal ``expression``/``round``
  attributes onto the rendered input.
- Fix list pagination leaking Turbo listeners on a failed page visit.
- Fix ``manage.py check``/``runserver`` crashing when a Join-node flow
  is defined outside any ``INSTALLED_APPS`` entry (e.g. a diagram-only
  flow at the project root).

2.3.1  2026-06-30
-----------------

- Add Django 6.1 support.
- Fix the bulk task assign/unassign actions not enforcing per-task
  ``can_assign``/``can_unassign`` permission.
- Fix the REST ``View``-node ``GET`` endpoint serving task data without a
  ``view`` permission check.
- Fix task views accepting a task pk from another flow; the task is now scoped to
  the flow in the URL.

2.3.0  2026-06-30
-----------------

- Fix ``viewflow.fsm`` chart generation crashing for ``Enum`` states and
  ``State.ANY`` markers; chart sorting no longer relies on states or transitions
  being orderable (#476).
- Use the localized status label (``get_status_display``) instead of the raw
  value in the default Task and Process briefs (#504).
- Add a ``building-with-viewflow`` skill for AI coding assistants (``skill/``,
  beta), and ship machine-readable docs for LLMs — ``llms.txt``,
  ``llms-full.txt`` and ``AGENTS.md`` on docs.viewflow.io (#498).
- Fix the ``vf-field-input`` ``readonly`` attribute not being treated as a
  boolean: it now defaults to ``false`` and is coerced like ``disabled`` and
  ``required`` (#499). Applied the same boolean coercion consistently across the
  field widgets (file ``multiple``/``disabled``, autocomplete, select-dependent),
  and added ``readonly`` support to ``vf-field-password`` and ``vf-field-textarea``.
- Fix process cancel being allowed with only view permission. Canceling a
  process now requires the ``manage`` permission, like the task cancel/undo/revive
  actions. ``Flow.has_view_permission`` and ``has_manage_permission`` now also
  honor object-level (e.g. django-guardian) permissions when an object is passed.
- Make ``Condition`` and ``Permission`` in ``viewflow.fsm.typing`` generic over
  the flow type. Typed predicates such as ``Callable[[Publication], bool]`` are
  now accepted at ``state.transition(conditions=...)`` without a cast, while all
  conditions in one list are still checked to share a compatible instance type.
- Update frontend and tooling dependencies to their latest within-major versions
  (the solid compiler, eslint, sass, material-icons, vis-network, trix and
  others). ``@material/web`` and ``solid-element`` are intentionally held back —
  newer releases break the web-component rendering.
- Upgrade the build to vite 7 (from 5) and vite-plugin-static-copy 4, clearing
  the vite/esbuild dev-server advisories. The ``@material`` typography mixin
  imports were migrated to the modern Sass ``@use`` API (``mdc-typography`` ->
  ``typography.typography``); the generated CSS is unchanged.
- Remove the unused legacy ``babel-core@4`` dev dependency (it pulled in a
  vulnerable lodash).
- Upgrade ``vanilla-jsoneditor`` 0.23 -> 3 (now bundles svelte 5), clearing the
  svelte advisories. The JSON field editor API is unchanged.

2.2.15  2025-12-24
------------------

- Fix form button name/value lost on resubmission after validation error with Turbo.
  The vf-form component was disabling buttons during submit before Turbo captured
  FormData, causing button values like _continue to be excluded.
- Fix subprocess double execution when completing synchronously.

2.2.14  2025-11-24
------------------

- Add Django 6.0 compatibility (requires Python 3.12+)
- Improve error handling for permission creation in multiple database configurations.
  Added helpful error message when IntegrityError occurs during permission creation,
  guiding users to properly configure database routers for the Permission model.
- Fix BPMN export to include name attribute for gateway nodes (flow.If).
  The flowexport command now properly exports gateway titles set via .Annotation(title="...").

2.2.13  2025-09-24
------------------

- Fix checkbox field error message styling to display in red color

2.2.12  2025-07-25
------------------

- Allow to extend and override process_data template


2.2.11 2025-05-14
-----------------

- Return .Avaialble(..) for the start node


2.2.10 2025-03-27
-----------------

- Add viewset get_form_class/get_create_form_class/get_update_form_class to allow per-request form customization for CRUD Views
- Add support for a trailing link to vf-field-input component
- Enhance vf-field-file to display a download link for existing files with automatic URL resolution
- Added FormAjaxCompleteMixin, FormDependentSelectMixin to default create and update workflow process views
- Extended patterns demo with user resources allocation samples https://demo.viewflow.io/patterns/resource_allocation/


2.2.9 2025-01-08
----------------

- Enhanced validation for flow_refs and task_refs to ensure accuracy and consistency.
- Resolved an issue with canceling processes containing revived tasks.
- Corrected the password reset confirmation email template for better functionality.
- Fixed multipart form type detection for forms with file fields in formsets.


2.2.8 2024-10-04
----------------

- Prevent exceptions from being raised by Process/Task models when a flow class
  is deleted but still referenced in the database.
- Fix serialization issue with jsonstore.DecimalField.
- Add missing 'index' view for celery.Task node.
- Enable recovery of flow.Subprocess and flow.NSubprocess nodes from error state.
- Correct invalid typing for FSM conditions.
- Allow setting permission=None in the FSM @transition decorator to explicitly bypass permission checks.
- Add support for MultiValueField and django-money fields form rendering

2.2.7 2024-08-16
----------------

- Added compatibility fix for Python 3.8.
- Extend documentation with data management explanation - https://docs.viewflow.io/workflow/data_flow.html
- Expanded documentation to cover permission management - https://docs.viewflow.io/workflow/permissions.html
- Introduced an experimental JSONEditorWidget.
- Fixed issue with saving the state of revived tasks.
- Enabled the option to cancel If tasks.
- Updated default FSM state change in FlowViewsMixin to now use transaction.atomic.
- Added support for using DependentModelSelect in formsets.
- Enabled AjaxModelSelect to function as a dependency for DependentModelSelect
- Corrected typo in the deletion success message.
- Test under django 5.1

2.2.6 2024-08-04
----------------

- Resolved the flow.If condition's this reference during class construction.
- Improved error handling when a Celery task finishes.
- Fixed an issue where errors occurring in a task after a successful celery.Job
  task incorrectly prevented the job task from being marked as completed, with
  the errored task correctly put into an error state.
- Redirect to the next process task now will take into account tasks in the ERROR state
- Add ability to revive flow.Function and flow.SplitFirst
- Fixed an error that occurred when a deleted process.artifact was referenced in
  the process field data listing within templates.
- Allow to cancel Subprocess tasks
- Allow to cancel Function tasks
- Allow custom task models inherited from AbstactTask have no .seed and .data fields


2.2.5 2024-07-17
-----------------

- The 'pattern' widget attribute is now passed to the underlying form input.
- Fixed issue with flow image reload.
- Fixed dashboard max height on pages with long sidebars.
- Added .get_success_url(request) shortcut method to StartViewActivation and
  ViewActivation for convenient use in function-based views.
- Fixed duplicated task_finished signal on flow.View completion.
- Enabled callable defaults on jsonstore fields.
- Improved SVG and BPMN export shapes for SplitFirst and Timer Tasks.
- Created cookbook demo for comon workflow patterns

2.2.4 2024-07-12
-----------------

- Clone data, seed, and artifacts from canceled tasks to revived tasks.
- Enhance error handling for celery.Job.
- Improve the process cancellation template.
- Redirect to the task detail page after canceling or undoing actions, instead
  of redirecting to the process detail page.
- Added links to parent subprocess and parent task on the subprocess process and
  task details pages.
- Updated the Process.parent_task field to use related_name='subprocess',
  allowing access to subprocesses via task.subprocess
- Enhanced CreateProcessView and UpdateProcessView to set process_seed and
  artifact_generic_foreign_key fields based on form.cleaned_data, as Django
  model forms do not handle this automatically.
- Added tasks with an ERROR status to the process dashboard for better visibility and tracking.
- Added tooltip hover titles to nodes without text labels in the SVG workflow graph.
- Marked StartHandler nodes as BPMN Start Message events on the SVG graph.
- Fixed rendering of hidden field errors in forms.

2.2.3 2024-07-09
-----------------

- Fixed issue with Split/Join operations when an immediate split to join
  connection occurs.
- Improved redirect functionality for "Execute and Continue." Now redirects to
  the process details if the process has finished.
- Enabled the Undo action for End() nodes.


2.2.2 2024-07-05
----------------

- Introduced new parameters for .If().Then(.., task_data=, task_seed) and
  .Else(...)
- Include {{ form.media }} into default workflow/task.html template


2.2.1 2024-07-03
----------------

- Introduced a new parameter for .Next(..., task_seed=) that allows the
  instantiation of new tasks with additional initialized .seed generic foreign key
- Introduced a new parameter for .Split(..., task_seed_source=) same as task_data_source,
  prodices outgoing tasks with initializaed .seed value
- Introduced a new parameter for flow.Subprocess(process_data=, process_seed=,
  task_data=, task_seed=) allows to provide data nad seed for newly created
  process and/or start task

2.2.0 2024-06-28
----------------

- Introduced a new parameter for .Next(..., task_data=) that allows the
  instantiation of new tasks with additional initialized .data, enabling data to
  be passed from task to task.
- Added process.seed and task.seed generic foreign keys to the default workflow
  models. Along with process.artifact and task.artifact, these additions enable
  tracking of business process results from start to finish.
- Renamed Split.Next(data_source=) to task_data_source=.

2.1.3 2024-06-26
----------------

- Allow to use `flow.StartHandle` as start for subprocess
- Subprocess got get_subprocess_kwargs callable to provide additional parameters to flow.StartHandle

2.1.2 2024-06-24
----------------

- Allow cancelling Celery tasks from the ERROR state.
- Hotfix: Fix broken Join when no other nodes are created by Split.
- Allow using this references to flow static methods as Celery tasks.
- Allow cancelling Celery jobs from the ERROR status.
- Add missing permission check before adding a new item to the list.
- Allow Admin() viewset to be used as a sub-item in an Application viewset.

2.1.1 2024-06-06
----------------

- Hotfix broken task creation

2.1.0 2024-06-16
----------------

- Allow to assign additional custom data to viewflow.fsm transitions
- Added `data_source` parameter to `Split.Next()` method, allowing dynamic creation of multiple node instances based on a list of data items.


2.0.3 2024-05-11
----------------

- Fix task titles on the task details pages


2.0.2 2024-04-19
----------------

- Fix logout link
- Change admin user autocomplete field to readonly

2.0.1 2024-04-17
----------------

- Fix for AjaxModelSelect in m2m relations


2.0.0 2024-04-09
----------------

- Added support for Django 5.0+
- Updated to Material Components Web 1.4.0
- Improved help text styles
- Fixed default app_name configuration for Viewsets
- List View initial filter values support
- Enhanced localization support
- Corrected object permission checks for delete actions

2.0.0.b8 2023-09-29
-------------------

- Fixed default values for jsonstore fields in forms.
- Pre-built workflow views now accept the layout option for forms.
- Improved success redirects for workflow action views.
- Enabled the 'Undo' action for celery.Job.
- Extended celery.Job activation to allow its use within the start and end tasks of celery.chord.
- Stored error traces and local variables in task.data JSON for failed celery.Job tasks.
- Enhanced handling of obsolete nodes.
- Fixed the JS calendar date shift issue for time zones with negative time offsets.


2.0.0.b7 2023-08-25
-------------------

- Fix pre-populated file field value
- Improvements for depended select widget
- Add total  counter widget
- Improve wizard template default breadcrumbs
- Support for %b date format

2.0.0.b6 2023-07-28
-------------------

- Fix label for File and Image fields

2.0.0.b5 2023-07-10
-------------------

- Alow attach layout to forms in default form rendering template
- Fix subprocess node activation
- Added db indexes for workflow models
- Improve workflow REST API support

2.0.0.b4 2023-06-05
-------------------

- New flow.SplitFirst Node
- New celery.Timer Node
- Expose REST API with drf-spectacular
- Expose list_ordering_fields in a ModelViewset
- Retain history and return to the Inbox/Queue list views after completing a flow task
- Enable smooth page transitions in Chrome/Safari
- Hotwire/Turbo integration for Django Admin with viewflow.contrib.admin app
- Resolved issue with viewflow.fsm reporting unmet condition messages

2.0.0.b3 2023-04-25
-------------------

- Fix migrations to BigAutoField
- Reintroduce workflow task signals


2.0.0.b2 2023-03-06
-------------------

- Revised and improved documentation https://docs.viewflow.io
- Extend autocomplete mixins for the formtools wizard support
- Add support for list_paginate_by count to the model viewset
- Virtual json fields got support in .values() and .values_list() queryset
- Add missing .js.map static files

2.0.0b1 2023-01-23
------------------
- Combined with django-material/django-fsm/jsonstore as a single package
- Switched to Google Material Components instead of MaterializeCSS
- Switched to hotwire/turbo instead of Turbolinks
- New Class-based URL configurations
- Composite FK support for legacy database for Django ORM
- Plotly dashboards integration
- Improved order of subsequent workflow tasks activations
- Many more improvements and fixes

1.11.0 2021-04-05
-----------------

- Django 4.0 fixes
- Simplify frontend task model customization


1.10.1 2021-12-10
-----------------

- Django 4.0 fixes


1.10.0 2021-11-12
-----------------

- Django 4.0 support
- Fix set assigned time on auto-assign
- Allow anonymous users to trigger flow start


1.9.0 2021-04-30
----------------

- Add additional template blocks for left panel. Close #311
- Fix issue with task assign on default POST
- Fix Spanish translation
- Add Italian translation
- Add custom rollback to update_status migration


1.8.1 2021-01-15
----------------

* Fix this-references for flow.Function task loader


1.8.0 2021-01-07
----------------

* Clean Django 4.0 warnings
* Allow flow.Handler redefinition with inheritance


1.7.0 2020-11-18
----------------

* Fix TaskQuerySet.user_queue filtering. Remove django 1.8 compatibility code


1.6.1 2020-05-13
----------------

* Fix auto permission creation for flow.View nodes
* Make django-rest-swagger requirements optional
* Fix REST Charts on python 3+


1.6.0 2019-11-19
----------------

* Django 3.0 support
* Add process.artifact and task.artifact generic fk fields for default models
* Add process.data and task.data generic json field for default models
* Add View().OnCreate(...) callback support
* Allow to override flow view access by Flow.has_view_permission method


1.5.3 2019-04-23
----------------

* Resolve this-references for Split and Switch nodes conditions


1.5.1 2019-02-25
----------------

* Task description field became rendered as django template with {{ process }} and {{ task }} variable available


1.5.0 2019-02-13
----------------

* Added portuguese translation


1.4.0 2018-10-25
----------------

* WebComponent based frontend (compatibility with django-material 1.4.x)
* Django 2.1 support
* [PRO] Flow chart internationalization


1.3.0 2018-08-23
----------------

* Django 2.1 support
* Support task permission checks on user model subclasses
* [PRO] django-rest-swagger 2.2.0 support


1.2.5 2018-05-07
----------------

* Fix process description translation on django 2.0
* Fix process dump data on django 2.0
* [PRO] Frontend - fix page scroll on graph model open


1.2.2 2018-02-26
----------------

* Fix admin actions menu
* Fix this-reference usage in If-node condition.
* [PRO] Expose Celery Retry task action
* [PRO] Fix obsolete node url resolve

1.2.0 2017-12-20
----------------

* Django 2.0 support
* Drop compatibility with Django 1.8/1.9/1.10
* Materialize 1.0.0 support

1.1.0 2017-11-01
----------------
* Fix prefetch_related usage on process and task queryset
* Fix runtime error in python2.7/gunicorn deployment
* [PRO] REST API support

1.0.0 2017-05-29
----------------

* Django 1.11 support
* Open-sourced Python 2.7 support
* Added AGPL license additional permissions (allows to link with commercial software)
* Localization added: German/French/Spanish/Korean/Chinese
* Improved task detail UI in frontend
* Frontend - task management menu fix
* `JobActivation.async` method renamed to `run_async`. Fix python 3.7 reserved word warning.
* [PRO] New process dashboard view
* [PRO] Django-Guardian support for task object level permissions
* [PRO] Fixes and improvements in the flow chart rendering


0.12.0 - 2017-02-14
-------------------

This is the cumulative release with many backward incompatibility changes.

* Django 1.6 now longer supported.

* Frontend now a part of the open-source package.

* Flow chart visualization added

* Every _cls suffix, ex in flow_cls, activation_cls, was renamed to
  _class. The reason for that is just to be consistent with django
  naming theme.

* Django-Extra-Views integration is removed. This was a pretty creepy
  way to handle Formsets and Inlines within django class-based
  views. Instead, django-material introduce a new way to handle Form
  Inlines same as a standard form field. See details in the
  documentation.

* Views are no longer inherits and implement an Activation
  interface. This change makes things much simple internally, and
  fixes inconsistency, in different scenarios. @flow_view,
  @flow_start_view decorators are no longer callable.

* Activation now passed as a request attribute. You need to remove
  explicit activation parameter from view function signature, and use
  request.activation instead.

* Built-in class based views are renamed, to be more consistent. Check
  the documentation to find a new view name.

* If().OnTrue().OnFalse() renamed to If().Then().Else()

* All conditions in If, Switch and other nodes receives now a node
  activation instance instead of process. So you can gen an access to
  the current task via activation.task variable.

* Same for callable in the .Assign() and .Permissions definitions.

* task_loader not is the attribute of a flow task. In makes functions
  and signal handlers reusable over different flows.

* Flow namespace are no longer hard-coded. Flow views now can be
  attached to any namespace in a URL config.

* flow_start_func, flow_start_signal decorators need to be used for
  the start nodes handlers. Decorators would establish a proper
  locking avoids concurrent flow process modifications in the
  background tasks.

* To use celery job with django 1.8, django-transaction-hooks need to
  be enabled.
