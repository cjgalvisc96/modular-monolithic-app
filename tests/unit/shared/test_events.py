from __future__ import annotations

from todo_app.contexts.shared.domain.entities.aggregate import AggregateRoot
from todo_app.contexts.shared.domain.events.base import DomainEvent


def test_aggregate_records_and_pulls_events():
    agg = AggregateRoot()
    agg.record_event(DomainEvent())
    agg.record_event(DomainEvent())
    events = agg.pull_events()
    assert len(events) == 2
    # pulling clears the buffer
    assert agg.pull_events() == []


def test_event_name_and_metadata():
    event = DomainEvent()
    assert event.name == "DomainEvent"
    assert event.event_id is not None
    assert event.occurred_at is not None
