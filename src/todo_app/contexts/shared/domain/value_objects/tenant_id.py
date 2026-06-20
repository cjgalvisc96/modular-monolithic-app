"""Tenant identity — the value carried from a Cognito claim down to RLS."""

from __future__ import annotations

from todo_app.contexts.shared.domain.value_objects.identifier import EntityId


class TenantId(EntityId):
    """Identifies the tenant that owns an aggregate.

    Bound to the DB transaction (`SET LOCAL app.tenant_id`) and enforced by RLS.
    """
