"""Domain-level exceptions shared across all bounded contexts.

These are framework-agnostic: presentation layers map them to transport-specific
responses (HTTP status codes, CLI exit codes), but the domain never knows about them.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class DomainValidationError(DomainError):
    """A value object or entity invariant was violated."""


class EntityNotFoundError(DomainError):
    """A requested aggregate does not exist (within the current tenant scope)."""

    def __init__(self, entity: str, identifier: object) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} not found: {identifier}")


class ConflictError(DomainError):
    """An operation conflicts with an existing aggregate (e.g. uniqueness)."""


class PermissionDeniedError(DomainError):
    """The acting principal is not allowed to perform the operation."""


class AuthenticationError(DomainError):
    """Authentication failed (e.g. an invalid or expired token).

    Lives in the shared kernel so the presentation layer can catch it without
    importing any context's infrastructure (the concrete auth adapter).
    """
