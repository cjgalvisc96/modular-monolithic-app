from uuid import uuid4

import pytest

from todo_app.contexts.shared.domain.exceptions import DomainValidationError
from todo_app.contexts.shared.domain.value_objects.email import Email
from todo_app.contexts.shared.domain.value_objects.identifier import EntityId
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId


class TestEmail:
    def test_normalizes_case_and_whitespace(self):
        assert Email("  Foo@Bar.COM ").value == "foo@bar.com"

    @pytest.mark.parametrize("bad", ["", "no-at", "a@b", "a@b@c.com", "x@y."])
    def test_rejects_invalid(self, bad):
        with pytest.raises(DomainValidationError):
            Email(bad)

    def test_str(self):
        assert str(Email("a@b.com")) == "a@b.com"


class TestEntityId:
    def test_generate_is_unique(self):
        assert EntityId.generate() != EntityId.generate()

    def test_from_string_roundtrip(self):
        u = uuid4()
        assert EntityId.from_string(str(u)).value == u

    def test_from_string_invalid(self):
        with pytest.raises(DomainValidationError):
            EntityId.from_string("not-a-uuid")

    def test_requires_uuid(self):
        with pytest.raises(DomainValidationError):
            EntityId("nope")  # type: ignore[arg-type]

    def test_tenant_id_is_entity_id(self):
        assert isinstance(TenantId.generate(), EntityId)
