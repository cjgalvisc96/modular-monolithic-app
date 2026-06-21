"""Tenant identity — the value carried from a Cognito claim down to RLS."""

from todo_app.contexts.shared.domain.value_objects.identifier import EntityId


class TenantId(EntityId):
    """Tenant that owns an aggregate; bound to the DB transaction and enforced by RLS."""
