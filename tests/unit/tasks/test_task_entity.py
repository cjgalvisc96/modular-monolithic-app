from datetime import date

import pytest

from todo_app.contexts.shared.domain.exceptions import DomainValidationError
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task
from todo_app.contexts.tasks.domain.value_objects.task_status import TaskStatus


def _create(**kw) -> Task:
    defaults = {
        "tenant_id": TenantId.generate(),
        "owner_id": OwnerId.generate(),
        "title": "Write tests",
    }
    defaults.update(kw)
    return Task.create(**defaults)


def test_create_emits_event_and_defaults_pending():
    task = _create()
    assert task.status is TaskStatus.PENDING
    assert [e.name for e in task.pull_events()] == ["TaskCreated"]


def test_blank_title_rejected():
    with pytest.raises(DomainValidationError):
        _create(title="  ")


def test_complete_emits_event_and_is_idempotent():
    task = _create()
    task.pull_events()
    task.complete()
    assert task.status is TaskStatus.COMPLETED
    assert [e.name for e in task.pull_events()] == ["TaskCompleted"]
    task.complete()  # idempotent — no second event
    assert task.pull_events() == []


def test_start_then_running():
    task = _create()
    task.start()
    assert task.status is TaskStatus.IN_PROGRESS


def test_start_completed_rejected():
    task = _create()
    task.complete()
    with pytest.raises(DomainValidationError):
        task.start()


def test_update_details():
    task = _create()
    task.update_details(title="New", description="d", due_date=date(2026, 7, 1))
    assert task.title == "New"
    assert task.due_date == date(2026, 7, 1)


def test_update_blank_title_rejected():
    with pytest.raises(DomainValidationError):
        _create().update_details(title=" ")


def test_status_parse_invalid():
    with pytest.raises(DomainValidationError):
        TaskStatus.parse("archived")
