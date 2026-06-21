"""Framework-agnostic domain exceptions shared across all bounded contexts."""

from __future__ import annotations


class DomainError(Exception):
    pass


class DomainValidationError(DomainError):
    """A value object or entity invariant was violated."""


class EntityNotFoundError(DomainError):
    def __init__(self, entity: str, identifier: object) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} not found: {identifier}")


class ConflictError(DomainError):
    """An operation conflicts with an existing aggregate (e.g. uniqueness)."""


class PermissionDeniedError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass
