---
name: building-with-viewflow
description: Use when building a Django app with the Viewflow library — workflows (BPMN), CRUD viewsets, FSM state transitions, jsonstore process data, or Viewflow forms. Loads Viewflow conventions and the full docs.
---

# Building with Viewflow

Viewflow is a low-code library for Django. It adds workflows (BPMN), CRUD,
forms, and reporting on top of normal Django models and views.

## How to use this skill

1. Fetch `https://docs.viewflow.io/llms-full.txt` — the whole documentation in
   one file. Search it before guessing an API. It is the source of truth.
2. For a quick orientation, fetch `https://docs.viewflow.io/AGENTS.md`.
3. Follow the conventions below.

## Conventions

- Install: `pip install django-viewflow`. Add `"viewflow"` (and
  `"viewflow.workflow"` for workflows) to `INSTALLED_APPS`.
- Workflows are `flow.Flow` subclasses; wire nodes with `this.<name>`. Store
  process data in `viewflow.jsonstore` fields on a proxy `Process` model — no
  per-field migrations.
- Mount with `Site`/`Application` viewsets, not hand-written URL patterns.
- For state transitions without the workflow engine, use `viewflow.fsm.State`
  and `@state.transition(source=..., target=...)`. The target state is set
  before the method body runs and rolls back on exception.
- A transition permission is a query, not a gate: the method runs regardless.
  Check `flow.<transition>.has_perm(user)` in the view and raise
  `PermissionDenied`.
- Workflow permissions are `view_<model>` and `manage_<model>`; canceling a
  process needs `manage`.
- Don't edit `viewflow/` in the open-source repo — it is generated.

## Examples

See `https://docs.viewflow.io/AGENTS.md` for minimal flow, URL, and FSM
examples, and https://github.com/viewflow/cookbook for full sample projects.
