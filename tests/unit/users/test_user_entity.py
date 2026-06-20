from __future__ import annotations

import pytest

from todo_app.contexts.shared.domain.exceptions import DomainValidationError
from todo_app.contexts.shared.domain.value_objects.email import Email
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.users.domain.entities.user import User
from todo_app.contexts.users.domain.value_objects.role import Role


def _register(**kw) -> User:
    defaults = {
        "tenant_id": TenantId.generate(),
        "email": Email("a@b.com"),
        "full_name": "Ann Lee",
    }
    defaults.update(kw)
    return User.register(**defaults)


class TestRegister:
    def test_emits_user_registered_event(self):
        user = _register(role=Role.ADMIN)
        events = user.pull_events()
        assert [e.name for e in events] == ["UserRegistered"]
        assert user.role is Role.ADMIN
        assert user.is_active

    def test_trims_full_name(self):
        assert _register(full_name="  Bob  ").full_name == "Bob"

    def test_blank_name_rejected(self):
        with pytest.raises(DomainValidationError):
            _register(full_name="   ")


class TestMutations:
    def test_rename(self):
        user = _register()
        user.rename("New Name")
        assert user.full_name == "New Name"

    def test_rename_blank_rejected(self):
        with pytest.raises(DomainValidationError):
            _register().rename(" ")

    def test_change_role(self):
        user = _register()
        user.change_role(Role.ADMIN)
        assert user.role.is_admin

    def test_deactivate(self):
        user = _register()
        user.deactivate()
        assert not user.is_active


class TestRole:
    def test_parse_case_insensitive(self):
        assert Role.parse("ADMIN") is Role.ADMIN

    def test_parse_invalid(self):
        with pytest.raises(DomainValidationError):
            Role.parse("superuser")
